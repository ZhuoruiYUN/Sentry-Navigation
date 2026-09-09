"""Launch the configurable RMUL 2026 3v3 field in Gazebo Classic 11."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    field_share = get_package_share_directory("rm2026_field")
    gazebo_share = get_package_share_directory("gazebo_ros")
    world_path = os.path.join(field_share, "worlds", "rmul_2026_3v3.world")

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gazebo_share, "launch", "gazebo.launch.py")
        ),
        launch_arguments={
            "world": world_path,
            "gui": LaunchConfiguration("gui"),
            "verbose": LaunchConfiguration("verbose"),
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument("gui", default_value="true"),
        DeclareLaunchArgument("verbose", default_value="false"),
        gazebo,
    ])
