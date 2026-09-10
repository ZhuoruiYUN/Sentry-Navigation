from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
import os


def scan_converter():
    return Node(
        package="pointcloud_to_laserscan",
        executable="pointcloud_to_laserscan_node",
        name="mid360_to_scan",
        output="screen",
        parameters=[{
            "use_sim_time": True, "target_frame": "base_link",
            "transform_tolerance": 0.1, "min_height": 0.10, "max_height": 0.50,
            "angle_min": -3.141593, "angle_max": 3.141593,
            "angle_increment": 0.004363323, "scan_time": 0.1,
            # Ignore MID360 returns from its own bracket/chassis near 0.15 m.
            "range_min": 0.25, "range_max": 30.0, "use_inf": True, "inf_epsilon": 1.0,
        }],
        remappings=[("cloud_in", "/mid360/points"), ("scan", "/scan")],
    )


def generate_launch_description():
    nav2 = get_package_share_directory("nav2_bringup")
    package_share = get_package_share_directory("sentry_navigation")
    params_file = os.path.join(package_share, "config", "nav2_sentry.yaml")
    map_yaml = LaunchConfiguration("map")
    initial_x = LaunchConfiguration("initial_x")
    initial_y = LaunchConfiguration("initial_y")
    initial_yaw = LaunchConfiguration("initial_yaw")
    return LaunchDescription([
        DeclareLaunchArgument("map", description="Absolute path to a saved map YAML file"),
        DeclareLaunchArgument("initial_x", default_value="-4.8"),
        DeclareLaunchArgument("initial_y", default_value="2.8"),
        DeclareLaunchArgument("initial_yaw", default_value="0.0"),
        scan_converter(),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(nav2, "launch", "localization_launch.py")),
            launch_arguments={"map": map_yaml, "use_sim_time": "true", "params_file": params_file}.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(nav2, "launch", "navigation_launch.py")),
            launch_arguments={"use_sim_time": "true", "params_file": params_file}.items(),
        ),
        # AMCL does not publish map->odom until it receives an initial pose.
        # Delay publication until the lifecycle manager has activated AMCL.
        TimerAction(period=3.0, actions=[
            Node(
                package="sentry_navigation",
                executable="set_initial_pose.py",
                name="sentry_initial_pose",
                output="screen",
                parameters=[{
                    "use_sim_time": True,
                    "x": ParameterValue(initial_x, value_type=float),
                    "y": ParameterValue(initial_y, value_type=float),
                    "yaw": ParameterValue(initial_yaw, value_type=float),
                }],
            ),
        ]),
    ])
