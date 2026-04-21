# Damped Track Chain – Blender
![图标](/icon.png)

[English](#english) | [中文](#中文)

---


## 中文

这是一个简单的 Blender 插件。

### ✨ 功能特性

- **一键生成骨骼链约束** – 选中链的根骨骼，点击按钮，每一节子骨骼都会自动获得指向其直接父级的阻尼追踪约束。
- **渐变影响值控制** – 可设定起始影响值和变化步长，影响值能够沿链**递减**或**递增**，让你精细控制每一段骨骼的跟随强度。
- **多链批量处理** – 支持同时选中多根根骨骼，每条链独立处理。
- **安全清理** – 提供专用的**清除**按钮，一键移除所选骨骼链上的所有阻尼追踪约束，不会误删手动添加的其他约束。
- **友好的界面面板** – 在姿态模式下，所有设置项都集成在 3D 视图右侧边栏（按 `N` 键展开）的 `Rigging` 选项卡中。

### 📦 安装方法

1. 下载本仓库的最新版本插件文件（`damped_track_chain.py`）。
2. 在 Blender 中打开 **编辑 > 偏好设置 > 插件**。
3. 点击右上角的 **安装…**，选择下载好的 `.zip` 文件。
4. 在插件列表中勾选启用 **Rigging: Damped Track Chain**。

### 🚀 使用方法

1. 选中你的骨架，进入 **姿态模式**。
2. 按下 `N` 键展开右侧边栏，找到 **Damped Track Chain** 面板（位于 `Rigging` 分类下）。
3. 根据需要调整参数：
   - **起始影响值** – 链中第一个约束（根骨骼 → 第一子骨骼）的影响强度。
   - **变化步长** – 每深入一级子骨骼，影响值变化的大小。
   - **变化方式** – 选择影响值沿链**递减**还是**递增**。
   - **追踪轴** – 指向目标骨骼的局部坐标轴（通常保持默认的 `Y` 轴即可）。
4. 在视图中选中一条或多条链的**根骨骼**。
5. 点击 **添加链** 按钮，约束即被自动创建。
6. 如需移除，选中根骨骼后点击 **清除链** 即可。

---

## English

This is a simple Blender add-on.

### ✨ Features

- **One-click bone chain constraints** – Select the root bone(s) of a chain, click the button, and every child bone automatically gets a Damped Track constraint pointing to its direct parent.
- **Gradient influence control** – Set a start influence value and a step value; influence can **decrease** or **increase** along the chain, giving you fine control over the follow strength of each segment.
- **Batch processing for multiple chains** – Supports selecting multiple root bones at once; each chain is processed independently.
- **Safe cleanup** – A dedicated **Clear** button removes all Damped Track constraints from the selected bone chains without deleting manually added constraints.
- **User-friendly panel** – In Pose Mode, all settings are integrated into the `Rigging` tab of the 3D View sidebar (press `N` to reveal).

### 📦 Installation

1. Download the latest add-on file (`damped_track_chain.py`) from this repository.
2. In Blender, go to **Edit > Preferences > Add-ons**.
3. Click **Install…** (top-right), select the downloaded `.zip` file.
4. Enable the add‑on by checking **Rigging: Damped Track Chain** in the list.

### 🚀 Usage

1. Select your armature and enter **Pose Mode**.
2. Press `N` to open the right sidebar, find the **Damped Track Chain** panel (under the `Rigging` category).
3. Adjust the parameters as needed:
   - **Start Influence** – Influence strength of the first constraint (root bone → first child).
   - **Step Value** – Amount the influence changes per bone deeper in the chain.
   - **Change Direction** – Choose whether influence **decreases** or **increases** along the chain.
   - **Track Axis** – The local axis that points toward the target bone (usually keep the default `Y` axis).
4. In the viewport, select the **root bone(s)** of one or more chains.
5. Click **Add Chain** – constraints are created automatically.
6. To remove constraints, select the root bone(s) and click **Clear Chain**.
