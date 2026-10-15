# Sentry navigation

## Navigate in Gazebo

Open three terminals in the workspace. Run `source env.sh` in each terminal.

1. Start the field and robot:

```bash
cd ~/Desktop/workspace/sentry-navigation
source env.sh
ros2 launch sentry_description gazebo.launch.py
```

2. Start localization and Nav2 with the completed simulation map:

```bash
cd ~/Desktop/workspace/sentry-navigation
source env.sh
ros2 launch sentry_navigation localization.launch.py \
  map:=$PWD/maps/rmul_3v3_v2.yaml
```

3. Open RViz:

```bash
cd ~/Desktop/workspace/sentry-navigation
source env.sh
ros2 launch sentry_navigation mapping_rviz.launch.py
```

Wait until the map and live `2D Scan` appear and RViz shows `Global Status: OK`.
Click **2D Goal Pose** in RViz, click a free point on the map, and drag to set
the final heading. Nav2 plans a route and sends velocity commands through the
lidar safety guard. The default spawn pose is `(-4.8, 2.8, 0)`; if you change
the Gazebo spawn coordinates, pass matching `initial_x`, `initial_y`, and
`initial_yaw` arguments to `localization.launch.py`.

The older `rmul_3v3.yaml` map has drift and should not be used for navigation.
Do not run `mapping.launch.py` at the same time as `localization.launch.py`:
both provide a map and a `/scan` converter.

## Build a new map

Start Gazebo first, then start mapping:

```bash
ros2 launch sentry_navigation mapping.launch.py
```

Drive with `/cmd_vel`, then save the map:

```bash
ros2 run nav2_map_server map_saver_cli -f maps/<new_name>
```
