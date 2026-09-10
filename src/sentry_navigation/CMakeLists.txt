cmake_minimum_required(VERSION 3.8)
project(sentry_navigation)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch config DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/sentry_teleop_gui.py scripts/set_initial_pose.py DESTINATION lib/${PROJECT_NAME})
ament_package()
