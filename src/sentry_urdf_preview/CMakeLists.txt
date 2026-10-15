cmake_minimum_required(VERSION 3.8)
project(sentry_urdf_preview)

find_package(ament_cmake REQUIRED)
install(DIRECTORY launch meshes models rviz urdf worlds DESTINATION share/${PROJECT_NAME})
ament_package()
