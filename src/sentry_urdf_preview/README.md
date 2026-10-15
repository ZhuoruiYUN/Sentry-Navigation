# CAD URDF preview

This package imports the supplied `sentry-urdf.zip` for ROS 2 RViz viewing. The
mesh URI package name was changed to `sentry_urdf_preview`. The 2,111,881-face
base STL was reduced to about 450,000 faces because the original stalled RViz.
The four empty wheel visuals and collisions were removed to avoid mesh errors.
Other CAD geometry, joint transforms, and exported dynamics are unchanged.
The original archive remains at
`/home/terry/Desktop/workspace/sentry-urdf.zip` outside this repository.

The captured RViz view is in `docs/sentry-cad-preview.png` at the repository
root.

```bash
source env.sh
ros2 launch sentry_urdf_preview display.launch.py
```

For a Gazebo Classic visual preview:

```bash
source env.sh
ros2 launch sentry_urdf_preview gazebo.launch.py
```

This starts a self-contained Gazebo Classic scene with the CAD model at the
origin. The model is static and has no collision or drive physics because the
CAD export lacks usable wheel geometry.

The four wheel STL files are empty (0 triangles), so they are invisible. All
five movable joints have zero position, effort, and velocity limits in the
export. The model also has no MID360, `base_link`, `livox_frame`, ROS 2 control,
or Gazebo sensor setup. It is therefore a visual preview only and is not wired
into the navigation simulation.
