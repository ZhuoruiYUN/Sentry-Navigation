from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    config = os.path.join(
        get_package_share_directory("sentry_navigation"), "config", "mapping.rviz"
    )
    return LaunchDescription([
        Node(
            package="rviz2",
            executable="rviz2",
            arguments=["-d", config],
            parameters=[{"use_sim_time": True}],
            output="screen",
        )
    ])
