# SolidWorks sentry preview

This ROS 2 package previews the SolidWorks export in
`/home/terry/Desktop/workspace/sentry.rar`. The optimized meshes are also used
by the active navigation robot in `sentry_description`. The earlier
`sentry_urdf_preview` package remains a separate visual comparison.

```bash
source env.sh
ros2 launch sentry_solidworks_preview gazebo.launch.py
```

The Gazebo Classic preview uses port `11347` and shows the CAD body, yaw
assembly, four armor plates, and all four wheels. The model is static; it is
for visual inspection only. A verified screenshot is saved at
`docs/sentry-solidworks-gazebo.png` in the workspace root. For a view of the
URDF link hierarchy in RViz:

```bash
ros2 launch sentry_solidworks_preview display.launch.py
```

The preview URDF keeps the exported link and joint transforms, with mesh URIs
changed to this ROS 2 package. The collision meshes were omitted from the
preview. The original 2,226,761-triangle base and 436,529-triangle yaw STL
were simplified for responsive viewing to 546,628 and 178,799 triangles,
respectively. Wheel and armor meshes retain their original geometry. The
original archive is unchanged.

The standalone preview is static. For a moving robot with the MID360 sensor,
navigation frames, ROS 2 control, and Nav2, use `sentry_description` and follow
`src/sentry_navigation/README.md` from the workspace root. The active simulator
uses planar kinematic motion; the CAD wheel joints are visual links.
