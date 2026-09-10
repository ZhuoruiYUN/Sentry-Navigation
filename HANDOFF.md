# Sentry Navigation Handoff

> This document is intentionally local-only and must not be committed.

## Current working state

- Ubuntu 22.04, ROS 2 Humble, Gazebo Classic 11.
- Workspace: `/home/terry/Desktop/workspace/sentry-navigation`.
- ROS domain: `42`; every terminal must start with `source env.sh`.
- Git remote: `git@github.com:ZhuoruiYUN/Sentry-Navigation.git`.
- The completed simulation map is `maps/rmul_3v3_v2.yaml` at 2.5 cm resolution. The older `rmul_3v3` map is known to contain SLAM drift and should not be used for navigation.

## Normal startup

Use separate terminals, always after `cd ~/Desktop/workspace/sentry-navigation` and `source env.sh`.

1. Gazebo and robot:

   ```bash
   ros2 launch sentry_description gazebo.launch.py
   ```

   This starts the field, sentry robot, lidar safety guard, gimbal controller, and the automatic MID360 gimbal scan sweep after five seconds.

2. Localization and Nav2:

   ```bash
   ros2 launch sentry_navigation localization.launch.py \
     map:=$HOME/Desktop/workspace/sentry-navigation/maps/rmul_3v3_v2.yaml
   ```

   The launch publishes the default spawn pose `(-4.8, 2.8, 0)` automatically. It now waits for AMCL discovery before publishing.

3. RViz:

   ```bash
   ros2 launch sentry_navigation mapping_rviz.launch.py
   ```

## Mapping workflow

For a fresh simulated map, run Gazebo, then:

```bash
ros2 launch sentry_navigation mapping.launch.py
ros2 run sentry_navigation sentry_teleop_gui.py
```

`mapping.launch.py` uses `slam_mapping_sim.yaml`: 2.5 cm map cells, Gazebo ground-truth odometry, scan matching and loop closure disabled. Save a new map with:

```bash
ros2 run nav2_map_server map_saver_cli -f maps/<new_name>
```

Never run mapping and localization simultaneously. Do not drag the robot in Gazebo or use RViz `2D Pose Estimate` while mapping.

## Navigation and safety

- Successful end-to-end target test: red spawn `(-4.8, 2.8)` to blue spawn `(4.8, -2.8)` through `/navigate_to_pose`.
- Gazebo's planar-motion plugin is kinematic and does not enforce rigid-body collision. Avoidance depends on Nav2 costmaps and `scan_safety_guard.py`.
- The guard routes `/cmd_vel` to `/cmd_vel_safe`, fails closed when scan data is stale, and stops at 0.55 m. Its LaserScan subscription must remain Best Effort.
- `nav2_sentry.yaml` uses an omni AMCL model, a conservative 0.40 m robot radius, and a 3-second lidar obstacle persistence window for the rotating gimbal's blind sector.
- The yaw gimbal sweeps from about `-86°` to `+86°`; do not run `gimbal_gui.py` alongside `gimbal_scan_sweep.py`.
- For real hardware, publish the measured gimbal yaw encoder into the same TF/joint-state chain; otherwise rotating-lidar points will be placed incorrectly.

## Useful checks

```bash
ros2 topic hz /scan
ros2 topic info /cmd_vel_safe --verbose
ros2 run tf2_ros tf2_echo map base_link
```

Before issuing a goal, RViz must show `Global Status: OK` and the live `2D Scan` must overlay map walls. Use `2D Goal Pose` for navigation; do not use `2D Pose Estimate` except to deliberately reinitialize AMCL.

## Files most likely to change next

- `src/sentry_description/urdf/sentry.urdf.xacro`: physical sensor offsets and vehicle geometry.
- `src/sentry_description/scripts/scan_safety_guard.py`: safety envelope and lidar coverage logic.
- `src/sentry_navigation/config/nav2_sentry.yaml`: footprint, costmaps, velocity limits and AMCL tuning.
- `src/sentry_navigation/config/slam_mapping.yaml`: real-MID360 SLAM configuration; retain scan matching for hardware.
