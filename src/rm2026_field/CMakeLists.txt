cmake_minimum_required(VERSION 3.8)
project(rm2026_field)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY config launch models worlds
  DESTINATION share/${PROJECT_NAME}
)

install(
  PROGRAMS scripts/generate_field.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()

