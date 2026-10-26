# RMUL 2027 3v3 官方 Gazebo 场地

<img src="assets/rmul_2027_3v3_gazebo.png" alt="RMUL 2027 官方 3v3 Gazebo 场地" width="60%">

机器人在 2027 场地中的仿真效果：

<img src="assets/sentry_in_rmul_2027_3v3.png" alt="哨兵机器人位于 RMUL 2027 场地中央控制区" width="85%">

默认场地由官方发布的 `RMUL2027_3V3_V1.0.0.stp` 转换而来。STEP 原件保存在
[`sources/`](sources/)；Gazebo 使用 [`models/rmul_2027_3v3_official/`](models/rmul_2027_3v3_official/)
中的网格。转换保留了 STEP 的九组表面颜色，并使用完整场地网格作为静态碰撞。
场地含边界的模型外廓约为 12.6 × 8.6 m，可比赛区域约为 12 × 8 m。

坐标单位为米，场地中心是原点：红方补给区在 `-X、+Y` 一侧，`+Z` 向上。
转换脚本将 STEP 的毫米坐标和向下为正的 CAD 竖直轴映射到 Gazebo 坐标。

## 启动

从工作空间根目录运行：

```bash
source env.sh
colcon build --symlink-install --packages-select rm2027_field sentry_description
ros2 launch rm2027_field rmul_2027_3v3.launch.py
```

如需在官方场地中加载哨兵，关闭上面的 Gazebo 后运行：

```bash
source env.sh
ros2 launch sentry_description gazebo.launch.py
```

一次只启动一个 Gazebo 场地。现有 `rmul_3v3_v2` 占据栅格地图对应 2026 场地。
2027 导航使用 `maps/rmul_2027_3v3_nav.yaml`，其中将官方模型里抬高的实体标记为
障碍，避免运动插件穿过高地。重新保存雷达地图后，运行
`python3 src/sentry_navigation/scripts/prepare_2027_nav_map.py` 更新导航地图。

## 更新官方模型

仓库已经包含转换后的 Gazebo 网格，正常启动不需要 Gmsh。若官方 STEP 更新，
替换 [`sources/RMUL2027_3V3_V1.0.0.stp`](sources/RMUL2027_3V3_V1.0.0.stp)，
安装 `python3-gmsh` 后重新生成：

```bash
sudo apt install python3-gmsh
/usr/bin/python3 src/rm2027_field/scripts/import_official_step.py
colcon build --symlink-install --packages-select rm2027_field
```
