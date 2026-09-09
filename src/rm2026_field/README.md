# RMUL 2026 3v3 Gazebo Field

该包提供用于 MID360 导航开发的可配置 3v3 场地。当前几何来自
`RMUL2026_3v3_Gazebo_Field_Spec.md`，官方值、推导值和仿真占位值均在配置中标注。

## 修改场地

只需编辑：

```text
config/field_config.json
```

然后重新生成 SDF 并编译：

```bash
cd ~/Desktop/workspace/sentry-navigation
python3 src/rm2026_field/scripts/generate_field.py
colcon build --symlink-install --packages-select rm2026_field
source install/setup.bash
```

未知的围墙高度和厚度位于 `perimeter_wall`，状态为 `simulation_only`。
红方位置是配置基准，蓝方位置由脚本按场地中心自动旋转 180 度生成。
高地护栏配置为高地纵向中间的 1.8 m 段；其起点距红方高地近端 0.9 m。

## 启动

```bash
source ~/Desktop/workspace/sentry-navigation/env.sh
ros2 launch rm2026_field rmul_2026_3v3.launch.py
```

无界面启动：

```bash
ros2 launch rm2026_field rmul_2026_3v3.launch.py gui:=false
```

世界文件是自包含的：不会下载 `model://sun` 或任何在线模型，离线也能启动。
