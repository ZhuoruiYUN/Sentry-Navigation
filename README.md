# Sentry Navigation

Robomaster 哨兵机器人导航开发工作空间，目标平台为 Ubuntu 22.04 + ROS 2 Humble。

## 当前内容

- `src/livox_ros_driver2`: Livox MID360 ROS 2 驱动
- `src/rm2026_field`: 可配置的 RMUL 2026 3v3 Gazebo 场地
- `env.sh`: ROS 2 Humble、工作空间和用户目录 SDK2 环境
- `config/`: 后续机器人、传感器和导航配置

## 环境

```bash
source ~/Desktop/workspace/sentry-navigation/env.sh
```

构建：

```bash
cd ~/Desktop/workspace/sentry-navigation
source /opt/ros/humble/setup.bash
colcon build --symlink-install
```

启动 3v3 场地：

```bash
source ~/Desktop/workspace/sentry-navigation/env.sh
ros2 launch rm2026_field rmul_2026_3v3.launch.py
```

场地规则变化时，编辑 `src/rm2026_field/config/field_config.json`，运行生成脚本后重新编译：

```bash
python3 src/rm2026_field/scripts/generate_field.py
colcon build --symlink-install --packages-select rm2026_field
```
