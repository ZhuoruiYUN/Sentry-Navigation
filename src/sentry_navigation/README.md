# Sentry navigation

Start Gazebo first, then start mapping:

```bash
source ~/Desktop/workspace/sentry-navigation/env.sh
ros2 launch sentry_navigation mapping.launch.py
```

Keep the gimbal yaw fixed while mapping. Drive with `/cmd_vel`, then save the map:

```bash
ros2 run nav2_map_server map_saver_cli -f ~/Desktop/workspace/sentry-navigation/maps/rmul_3v3
```

For localization and Nav2 after the map is saved:

```bash
ros2 launch sentry_navigation localization.launch.py \
  map:=$HOME/Desktop/workspace/sentry-navigation/maps/rmul_3v3.yaml
```
