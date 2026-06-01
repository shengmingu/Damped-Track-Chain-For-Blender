# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 shengmingu

import bpy
import os
from bpy.app.translations import pgettext_iface as pgettext
from . import translation

# ==================== 骨骼链获取函数 ====================
def get_bone_chain(start_bone, armature):
    """
    Traverse from the given start bone down the parent-child hierarchy,
    returning a list of bones in depth-first order.
    """
    chain = []
    
    def traverse(bone):
        chain.append(bone)
        for child in bone.children:
            traverse(child)
    
    traverse(start_bone)
    return chain

# ==================== 属性组 ====================
class DampedTrackChainSettings(bpy.types.PropertyGroup):
    """Store user settings for the Damped Track Chain add-on"""
    
    influence_start: bpy.props.FloatProperty(
        name=pgettext("Start Influence"),
        description=pgettext("Influence of the first constraint (root bone to first child)"),
        default=1.0,
        min=0.0,
        max=1.0,
    )
    
    influence_step: bpy.props.FloatProperty(
        name=pgettext("Step Value"),
        description=pgettext("Amount of influence change per bone deeper in the chain"),
        default=0.1,
        min=0.0,
        max=1.0,
    )
    
    direction_items = [
        ('DECREASE', pgettext("Decrease"), pgettext("Decrease influence for each child bone")),
        ('INCREASE', pgettext("Increase"), pgettext("Increase influence for each child bone")),
    ]
    
    step_direction: bpy.props.EnumProperty(
        name=pgettext("Direction"),
        description=pgettext("Direction of influence change along the chain"),
        items=direction_items,
        default='DECREASE',
    )
    
    track_axis: bpy.props.EnumProperty(
        name=pgettext("Track Axis"),
        description=pgettext("Local axis pointing to the target"),
        items=[
            ('TRACK_X', pgettext("X"), pgettext("Track X axis")),
            ('TRACK_Y', pgettext("Y"), pgettext("Track Y axis")),
            ('TRACK_Z', pgettext("Z"), pgettext("Track Z axis")),
            ('TRACK_NEGATIVE_X', pgettext("-X"), pgettext("Track negative X axis")),
            ('TRACK_NEGATIVE_Y', pgettext("-Y"), pgettext("Track negative Y axis")),
            ('TRACK_NEGATIVE_Z', pgettext("-Z"), pgettext("Track negative Z axis")),
        ],
        default='TRACK_Y',
    )

# ==================== 面板 ====================
class VIEW3D_PT_damped_track_chain(bpy.types.Panel):
    """Sidebar panel"""
    bl_label = pgettext("Damped Track Chain")
    bl_idname = "VIEW3D_PT_damped_track_chain"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = pgettext("Rigging")
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
        row.operator("pose.add_damped_track_chain", text=pgettext("Add Chain"), icon='ADD')
        row.operator("pose.remove_damped_track_chain", text=pgettext("Clear Chain"), icon='REMOVE')

        col.separator()
        col.operator("pose.select_damped_track_chain", text=pgettext("Select Chain Bones"), icon='BONE_DATA')

# ==================== 添加约束操作符 ====================
class POSE_OT_add_damped_track_chain(bpy.types.Operator):
    """Automatically add Damped Track constraints for selected bones and all their children, with influence gradient along the chain"""
    bl_idname = "pose.add_damped_track_chain"
    bl_label = pgettext("Add Damped Track Chain")
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
            self.report({'ERROR'}, pgettext("Please select bones in Pose Mode first"))
            return {'CANCELLED'}
        
        selected_pose_bones = context.selected_pose_bones
        if selected_pose_bones is None:
            self.report({'ERROR'}, pgettext("Unable to read selected pose bones, please retry"))
            return {'CANCELLED'}
        if len(selected_pose_bones) == 0:
            self.report({'WARNING'}, pgettext("No bones selected"))
            return {'CANCELLED'}
        
        selected_bone_names = [bone.name for bone in selected_pose_bones]
        original_mode = context.mode
        bpy.ops.object.mode_set(mode='OBJECT')
        
        processed_pairs = set()
        constraints_added = 0
        
        for start_bone_name in selected_bone_names:
            edit_bone = armature.bones.get(start_bone_name)
            if not edit_bone:
                self.report({'WARNING'}, pgettext("Cannot find bone: {}").format(start_bone_name))
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
                
                # Remove existing constraint with same target
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
            self.report({'INFO'}, pgettext("Successfully added {} Damped Track constraint(s)").format(constraints_added))
        else:
            self.report({'WARNING'}, pgettext("No constraints added, please check selected bones"))
        
        return {'FINISHED'}

# ==================== 选中链上骨骼操作符 ====================
class POSE_OT_select_damped_track_chain(bpy.types.Operator):
    """Select all bones that have Damped Track constraints in the active armature"""
    bl_idname = "pose.select_damped_track_chain"
    bl_label = pgettext("Select Chain Bones")
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
            self.report({'ERROR'}, pgettext("Please enter Pose Mode first"))
            return {'CANCELLED'}

        # Switch to EDIT mode to safely modify bone selection
        bpy.ops.object.mode_set(mode='EDIT')

        # Deselect all bones first
        for edit_bone in armature.edit_bones:
            edit_bone.select = False
            edit_bone.select_head = False
            edit_bone.select_tail = False

        selected_count = 0
        for edit_bone in armature.edit_bones:
            pose_bone = obj.pose.bones.get(edit_bone.name)
            if not pose_bone:
                continue
            for c in pose_bone.constraints:
                if c.type == 'DAMPED_TRACK' and c.name.startswith("DampedTrack_"):
                    if c.target == obj and c.subtarget:
                        edit_bone.select = True
                        selected_count += 1
                        break

        # Switch back to Pose Mode
        bpy.ops.object.mode_set(mode='POSE')

        if selected_count > 0:
            self.report({'INFO'}, pgettext("Selected {} bone(s) with Damped Track constraints").format(selected_count))
        else:
            self.report({'WARNING'}, pgettext("No bones with Damped Track constraints found"))

        return {'FINISHED'}

# ==================== 清除约束操作符 ====================
class POSE_OT_remove_damped_track_chain(bpy.types.Operator):
    """Remove Damped Track constraints from selected bone chain and all its children"""
    bl_idname = "pose.remove_damped_track_chain"
    bl_label = pgettext("Remove Damped Track Chain")
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
            self.report({'ERROR'}, pgettext("Please select bones in Pose Mode first"))
            return {'CANCELLED'}
        
        selected_pose_bones = context.selected_pose_bones
        if selected_pose_bones is None:
            self.report({'ERROR'}, pgettext("Unable to read selected pose bones, please retry"))
            return {'CANCELLED'}
        if len(selected_pose_bones) == 0:
            self.report({'WARNING'}, pgettext("No bones selected"))
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
            
            for i in range(len(chain) - 1):
                current_bone = chain[i]
                
                if current_bone.name in processed_bones:
                    continue
                processed_bones.add(current_bone.name)
                
                pose_current = obj.pose.bones.get(current_bone.name)
                if not pose_current:
                    continue
                
                to_remove = []
                for c in pose_current.constraints:
                    if c.type == 'DAMPED_TRACK':
                        if c.target == obj and c.subtarget:
                            to_remove.append(c)
                
                for c in to_remove:
                    pose_current.constraints.remove(c)
                    constraints_removed += 1
        
        bpy.ops.object.mode_set(mode=original_mode)
        
        if constraints_removed > 0:
            self.report({'INFO'}, pgettext("Successfully removed {} Damped Track constraint(s)").format(constraints_removed))
        else:
            self.report({'WARNING'}, pgettext("No constraints found to remove"))
        
        return {'FINISHED'}

# ==================== 注册/注销 ====================
classes = (
    DampedTrackChainSettings,
    VIEW3D_PT_damped_track_chain,
    POSE_OT_add_damped_track_chain,
    POSE_OT_remove_damped_track_chain,
    POSE_OT_select_damped_track_chain,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.damped_track_chain_settings = bpy.props.PointerProperty(type=DampedTrackChainSettings)
    translation.register_module()

def unregister():
    translation.unregister_module()
    del bpy.types.Scene.damped_track_chain_settings
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()