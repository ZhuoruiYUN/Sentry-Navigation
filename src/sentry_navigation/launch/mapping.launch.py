from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os


def scan_converter():
    return Node(
        package="pointcloud_to_laserscan",
        executable="pointcloud_to_laserscan_node",
        name="mid360_to_scan",
        output="screen",
        parameters=[{
            "use_sim_time": True,
            "target_frame": "base_link",
            "transform_tolerance": 0.1,
            "min_height": 0.10,
            "max_height": 0.50,
            "angle_min": -3.141593,
            "angle_max": 3.141593,
            "angle_increment": 0.004363323,
            "scan_time": 0.1,
            # Ignore MID360 returns from its own bracket/chassis near 0.15 m.
            "range_min": 0.25,
            "range_max": 30.0,
            "use_inf": True,
            "inf_epsilon": 1.0,
        }],
        remappings=[("cloud_in", "/mid360/points"), ("scan", "/scan")],
    )


def generate_launch_description():
    default_params = os.path.join(
        get_package_share_directory("sentry_navigation"),
        "config",
        "slam_mapping_sim.yaml",
    )
    params = LaunchConfiguration("params_file")
    return LaunchDescription([
        DeclareLaunchArgument(
            "params_file",
            default_value=default_params,
            description="slam_toolbox parameter file; defaults to Gazebo ground-truth odometry",
        ),
        scan_converter(),
        Node(
            package="slam_toolbox",
            executable="async_slam_toolbox_node",
            name="slam_toolbox",
            output="screen",
            parameters=[params],
        ),
    ])
