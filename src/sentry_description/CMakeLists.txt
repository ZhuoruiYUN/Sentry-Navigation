cmake_minimum_required(VERSION 3.8)
project(sentry_description)
find_package(ament_cmake REQUIRED)
install(DIRECTORY launch meshes rviz urdf config DESTINATION share/${PROJECT_NAME})
install(PROGRAMS
  scripts/gimbal_gui.py
  scripts/gimbal_scan_sweep.py
  scripts/scan_safety_guard.py
  DESTINATION lib/${PROJECT_NAME}
)
ament_package()
