bl_info = {
    "name": "Damped Track Chain",
    "author": "shengmingu",
    "version": (1, 0, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Damped Track Chain",
    "description": "为选中骨骼及其所有子级骨骼自动添加/清除阻尼追踪约束，可设置影响值沿链递减/递增，适合制作头发/尾巴的动态效果。",
    "category": "Rigging",
}

import bpy


def get_bone_chain(start_bone, armature):
    """
    从给定的起始骨骼开始，沿着父子层级向下遍历，
    返回按深度优先顺序排列的骨骼列表。
    """
    chain = []
    
    def traverse(bone):
        chain.append(bone)
        for child in bone.children:
            traverse(child)
    
    traverse(start_bone)
    return chain


class DampedTrackChainSettings(bpy.types.PropertyGroup):
    """存储阻尼追踪链插件的用户设置"""
    
    influence_start: bpy.props.FloatProperty(
        name="起始影响值",
        description="链中第一个约束（根骨骼到第一子骨骼）的影响值",
        default=1.0,
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
    )
    
    influence_step: bpy.props.FloatProperty(
        name="变化步长",
        description="每深入一级子骨骼，影响值的变化量",
        default=0.1,
        min=0.0,
        max=1.0,
        soft_min=0.0,
        soft_max=1.0,
    )
    
    direction_items = [
        ('DECREASE', "递减", "每级子骨骼的影响值减少"),
        ('INCREASE', "递增", "每级子骨骼的影响值增加"),
    ]
    
    step_direction: bpy.props.EnumProperty(
        name="变化方式",
        description="影响值沿链的变化方向",
        items=direction_items,
        default='DECREASE',
    )
    
    track_axis: bpy.props.EnumProperty(
        name="追踪轴",
        description="指向目标的局部坐标轴",
        items=[
            ('TRACK_X', "X", "追踪X轴"),
            ('TRACK_Y', "Y", "追踪Y轴"),
            ('TRACK_Z', "Z", "追踪Z轴"),
            ('TRACK_NEGATIVE_X', "-X", "追踪负X轴"),
            ('TRACK_NEGATIVE_Y', "-Y", "追踪负Y轴"),
            ('TRACK_NEGATIVE_Z', "-Z", "追踪负Z轴"),
        ],
        default='TRACK_Y',
    )


class VIEW3D_PT_damped_track_chain(bpy.types.Panel):
    """侧边栏面板"""
    bl_label = "Damped Track Chain"
    bl_idname = "VIEW3D_PT_damped_track_chain"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Rigging"
    bl_context = "posemode"
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'ARMATURE' and context.mode == 'POSE'
    
    def draw(self, context):
        layout = self.layout
        settings = context.scene.damped_track_chain_settings
        
        col = layout.column(align=True)
        col.prop(settings, "influence_start")
        col.prop(settings, "influence_step")
        col.prop(settings, "step_direction", expand=True)
        col.separator()
        col.prop(settings, "track_axis")
        
        col.separator()
        row = col.row(align=True)
        row.operator("pose.add_damped_track_chain", text="添加链", icon='ADD')
        row.operator("pose.remove_damped_track_chain", text="清除链", icon='REMOVE')


class POSE_OT_add_damped_track_chain(bpy.types.Operator):
    """为选中骨骼及其所有子骨骼自动添加阻尼追踪约束，影响值可沿链渐变"""
    bl_idname = "pose.add_damped_track_chain"
    bl_label = "Add Damped Track Chain"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj or obj.type != 'ARMATURE':
            return False
        return context.mode == 'POSE'
    
    def execute(self, context):
        obj = context.active_object
        armature = obj.data
        settings = context.scene.damped_track_chain_settings
        
        if context.mode != 'POSE':
            self.report({'ERROR'}, "请先在姿态模式下选中骨骼")
            return {'CANCELLED'}
        
        selected_pose_bones = context.selected_pose_bones
        if selected_pose_bones is None:
            self.report({'ERROR'}, "无法读取选中的姿态骨骼，请重试")
            return {'CANCELLED'}
        if len(selected_pose_bones) == 0:
            self.report({'WARNING'}, "没有选中任何骨骼")
            return {'CANCELLED'}
        
        selected_bone_names = [bone.name for bone in selected_pose_bones]
        original_mode = context.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        processed_pairs = set()
        constraints_added = 0
        
        for start_bone_name in selected_bone_names:
            edit_bone = armature.bones.get(start_bone_name)
            if not edit_bone:
                self.report({'WARNING'}, f"无法找到骨骼: {start_bone_name}")
                continue
            
            chain = get_bone_chain(edit_bone, armature)
            
            influence_values = []
            current_influence = settings.influence_start
            step_sign = -1 if settings.step_direction == 'DECREASE' else 1
            step = settings.influence_step * step_sign
            
            for i in range(len(chain) - 1):
                clamped = max(0.0, min(1.0, current_influence))
                influence_values.append(clamped)
                current_influence += step
            
            for idx, i in enumerate(range(len(chain) - 1)):
                current_bone = chain[i]
                next_bone = chain[i + 1]
                
                pair_id = (current_bone.name, next_bone.name)
                if pair_id in processed_pairs:
                    continue
                processed_pairs.add(pair_id)
                
                pose_current = obj.pose.bones.get(current_bone.name)
                if not pose_current:
                    continue
                
                # 移除同名旧约束
                for c in pose_current.constraints:
                    if c.type == 'DAMPED_TRACK':
                        if c.subtarget == next_bone.name:
                            pose_current.constraints.remove(c)
                            break
                
                constraint = pose_current.constraints.new(type='DAMPED_TRACK')
                constraint.name = f"DampedTrack_to_{next_bone.name}"
                constraint.target = obj
                constraint.subtarget = next_bone.name
                constraint.track_axis = settings.track_axis
                constraint.influence = influence_values[idx]
                
                constraints_added += 1
        
        bpy.ops.object.mode_set(mode=original_mode)
        
        if constraints_added > 0:
            self.report({'INFO'}, f"成功添加了 {constraints_added} 个阻尼追踪约束")
        else:
            self.report({'WARNING'}, "没有添加任何约束，请检查选中的骨骼")
        
        return {'FINISHED'}


class POSE_OT_remove_damped_track_chain(bpy.types.Operator):
    """清除选中骨骼及其所有子骨骼链上的阻尼追踪约束"""
    bl_idname = "pose.remove_damped_track_chain"
    bl_label = "Remove Damped Track Chain"
    bl_options = {'REGISTER', 'UNDO'}
    
    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj or obj.type != 'ARMATURE':
            return False
        return context.mode == 'POSE'
    
    def execute(self, context):
        obj = context.active_object
        armature = obj.data
        
        if context.mode != 'POSE':
            self.report({'ERROR'}, "请先在姿态模式下选中骨骼")
            return {'CANCELLED'}
        
        selected_pose_bones = context.selected_pose_bones
        if selected_pose_bones is None:
            self.report({'ERROR'}, "无法读取选中的姿态骨骼，请重试")
            return {'CANCELLED'}
        if len(selected_pose_bones) == 0:
            self.report({'WARNING'}, "没有选中任何骨骼")
            return {'CANCELLED'}
        
        selected_bone_names = [bone.name for bone in selected_pose_bones]
        original_mode = context.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        processed_bones = set()
        constraints_removed = 0
        
        for start_bone_name in selected_bone_names:
            edit_bone = armature.bones.get(start_bone_name)
            if not edit_bone:
                continue
            
            chain = get_bone_chain(edit_bone, armature)
            
            # 遍历链中每一根骨骼（除了最后一根，因为它没有子骨骼需要约束）
            for i in range(len(chain) - 1):
                current_bone = chain[i]
                
                # 避免对同一根骨骼重复处理
                if current_bone.name in processed_bones:
                    continue
                processed_bones.add(current_bone.name)
                
                pose_current = obj.pose.bones.get(current_bone.name)
                if not pose_current:
                    continue
                
                # 找到所有阻尼追踪约束，并移除指向子骨骼的那些
                to_remove = []
                for c in pose_current.constraints:
                    if c.type == 'DAMPED_TRACK':
                        # 只移除目标为骨架自身且子目标为某个骨骼的约束
                        if c.target == obj and c.subtarget:
                            # 检查子目标是否是当前骨骼的子骨骼（可选的安全检查）
                            # 简单起见，直接移除所有该类型的约束
                            to_remove.append(c)
                
                for c in to_remove:
                    pose_current.constraints.remove(c)
                    constraints_removed += 1
        
        bpy.ops.object.mode_set(mode=original_mode)
        
        if constraints_removed > 0:
            self.report({'INFO'}, f"成功移除了 {constraints_removed} 个阻尼追踪约束")
        else:
            self.report({'WARNING'}, "没有找到需要移除的约束")
        
        return {'FINISHED'}


classes = (
    DampedTrackChainSettings,
    VIEW3D_PT_damped_track_chain,
    POSE_OT_add_damped_track_chain,
    POSE_OT_remove_damped_track_chain,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.damped_track_chain_settings = bpy.props.PointerProperty(type=DampedTrackChainSettings)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.damped_track_chain_settings

if __name__ == "__main__":
    register()