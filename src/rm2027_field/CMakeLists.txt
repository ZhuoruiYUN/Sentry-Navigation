cmake_minimum_required(VERSION 3.8)
project(rm2027_field)

find_package(ament_cmake REQUIRED)

install(DIRECTORY assets launch models sources worlds DESTINATION share/${PROJECT_NAME})
install(PROGRAMS scripts/import_official_step.py DESTINATION lib/${PROJECT_NAME})

ament_package()
