# Sentry navigation

The robot's Gazebo launch loads the official 2027 field by default. Use
`maps/rmul_2027_3v3_nav.yaml` for Nav2. It combines the saved lidar map with
the official STEP model's raised geometry, preventing the planar simulator
from routing through highlands and tunnel plates. The original lidar map is
`maps/rmul_2027_3v3.yaml`. The 2026 map is separate.

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
  map:=$PWD/maps/rmul_2027_3v3_nav.yaml
```

3. Open RViz:

```bash
cd ~/Desktop/workspace/sentry-navigation
source env.sh
ros2 launch sentry_navigation mapping_rviz.launch.py
```

Wait until the map and live `2D Scan` appear, the scan aligns with the mapped
walls, and RViz shows `Global Status: OK`. Click **Nav2 Goal** in RViz, click
a nearby free point on the map, and drag to set the final heading. A path
should appear and Nav2 should send velocity commands through the lidar safety
guard. The default spawn pose is `(-4.8, 2.8, 0)`; if you change the Gazebo
spawn coordinates, pass matching `initial_x`, `initial_y`, and `initial_yaw`
arguments to `localization.launch.py`.

For the saved 2026 map instead, start Gazebo with `field_year:=2026` and pass
`map:=$PWD/maps/rmul_3v3_v2.yaml` to `localization.launch.py`.

The older `rmul_3v3.yaml` map has drift and should not be used for navigation.
Do not run `mapping.launch.py` at the same time as `localization.launch.py`:
both provide a map and a `/scan` converter.

## Build a new map

Start Gazebo with the default 2027 field, then start mapping and RViz in
separate terminals. Run `source env.sh` in each terminal:

```bash
ros2 launch sentry_description gazebo.launch.py
```

```bash
ros2 launch sentry_navigation mapping.launch.py
```

```bash
ros2 launch sentry_navigation mapping_rviz.launch.py
```

In a fourth terminal, run the project's manual-drive window. Click the window
before driving: W/S move forward/backward, A/D strafe, Q/E rotate, and Space
stops. Move through the traversable areas while checking that the map grows
in RViz:

```bash
ros2 run sentry_navigation sentry_teleop_gui.py
```

After covering the areas needed for navigation, save the 2027 map from the
workspace root in another terminal:

```bash
ros2 run nav2_map_server map_saver_cli -f maps/rmul_2027_3v3
```

After each new save, rebuild the navigation map from the lidar map and the
official field mesh:

```bash
python3 src/sentry_navigation/scripts/prepare_2027_nav_map.py
```

For localization in this field, pass `map:=$PWD/maps/rmul_2027_3v3_nav.yaml`
to `localization.launch.py`. Stop `mapping.launch.py` before starting
localization. Do not drag the robot in Gazebo or use RViz **2D Pose Estimate**
while mapping. The planar-motion plugin does not enforce rigid-body contact;
raised structures are marked as obstacles in the navigation map instead.
