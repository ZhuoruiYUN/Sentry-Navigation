# Sentry Navigation

Robomaster 哨兵机器人导航开发工作空间，目标平台为 Ubuntu 22.04 + ROS 2 Humble。

## 当前内容

- `src/livox_ros_driver2`: Livox MID360 ROS 2 驱动
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

