from launch import LaunchDescription
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    share = FindPackageShare("sentry_description")
    model = PathJoinSubstitution([share, "urdf", "sentry.urdf.xacro"])
    description = {
        "robot_description": ParameterValue(
            Command([FindExecutable(name="xacro"), " ", model]), value_type=str
        )
    }
    return LaunchDescription([
        Node(package="robot_state_publisher", executable="robot_state_publisher", parameters=[description]),
        Node(package="joint_state_publisher_gui", executable="joint_state_publisher_gui"),
        Node(package="rviz2", executable="rviz2", arguments=["-d", PathJoinSubstitution([share, "rviz", "sentry.rviz"])])])
