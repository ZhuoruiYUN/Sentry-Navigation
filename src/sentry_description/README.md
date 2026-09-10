# sentry_description

First-pass ROS 2 Humble model generated from supplied STEP exports.

- ROS axes: X front, Y left, Z up.
- STEP units are millimetres; mesh scale is 0.001.
- Pitch is rigid and included in gimbal_yaw_link.
- MID-360 housing is already in the yaw mesh; lidar_link is frame-only.
- Four armor links use primitive collision for independent contact sensing.
- Gazebo planar motion accepts vx, vy and wz.
- Masses, inertias and transforms are approximate and centralized for calibration.

Build and display:

    mkdir -p ~/sentry_ws/src
    cp -r sentry_description ~/sentry_ws/src/
    cd ~/sentry_ws
    colcon build --symlink-install
    source install/setup.bash
    ros2 launch sentry_description display.launch.py

Gazebo 3v3 field: ros2 launch sentry_description gazebo.launch.py

The Gazebo launch starts the local RMUL 2026 3v3 field and spawns the sentry
at `x=-4.8, y=2.8, z=0.01`. Override the spawn pose when needed, for example:

    ros2 launch sentry_description gazebo.launch.py x:=0 y:=-3 z:=0.01

Gmsh reported a few bad detailed CAD faces. Visual STLs were still generated;
primitive collision geometry is unaffected.
