"""Start the real MID-360 with topic names used by sentry_navigation."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    default_config = os.path.join(
        get_package_share_directory("livox_ros_driver2"), "config", "MID360_config.json"
    )
    rviz_config = os.path.join(
        get_package_share_directory("livox_ros_driver2"),
        "config",
        "display_point_cloud_ROS2.rviz",
    )
    return LaunchDescription([
        DeclareLaunchArgument("config", default_value=default_config),
        DeclareLaunchArgument("rviz", default_value="true"),
        Node(
            package="livox_ros_driver2",
            executable="livox_ros_driver2_node",
            name="livox_lidar_publisher",
            output="screen",
            parameters=[{
                "user_config_path": LaunchConfiguration("config"),
                "xfer_format": 0,
                "multi_topic": 0,
                "data_src": 0,
                "publish_freq": 10.0,
                "output_data_type": 0,
                "frame_id": "livox_frame",
            }],
            remappings=[
                ("livox/lidar", "/mid360/points"),
                ("livox/imu", "/mid360/imu"),
            ],
        ),
        Node(
            package="rviz2",
            executable="rviz2",
            name="mid360_rviz",
            output="screen",
            arguments=["--display-config", rviz_config],
            remappings=[("/livox/lidar", "/mid360/points")],
            condition=IfCondition(LaunchConfiguration("rviz")),
        ),
    ])
