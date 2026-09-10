from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

def generate_launch_description():
    share = FindPackageShare("sentry_description")
    field = FindPackageShare("rm2026_field")
    model = PathJoinSubstitution([share, "urdf", "sentry.urdf.xacro"])
    description = {
        "robot_description": ParameterValue(
            Command([FindExecutable(name="xacro"), " ", model, " use_gazebo:=true"]),
            value_type=str,
        )
    }
    return LaunchDescription([
        DeclareLaunchArgument("gui", default_value="true"),
        DeclareLaunchArgument("x", default_value="-4.8"),
        DeclareLaunchArgument("y", default_value="2.8"),
        DeclareLaunchArgument("z", default_value="0.01"),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                PathJoinSubstitution([field, "launch", "rmul_2026_3v3.launch.py"])
            ),
            launch_arguments={"gui": LaunchConfiguration("gui")}.items(),
        ),
        Node(package="robot_state_publisher", executable="robot_state_publisher", parameters=[description]),
        Node(
            package="sentry_description",
            executable="scan_safety_guard.py",
            output="screen",
        ),
        Node(
            package="gazebo_ros",
            executable="spawn_entity.py",
            arguments=[
                "-topic", "robot_description", "-entity", "sentry",
                "-x", LaunchConfiguration("x"),
                "-y", LaunchConfiguration("y"),
                "-z", LaunchConfiguration("z"),
            ],
            output="screen",
        ),
        # The model's GazeboSystem is available after SpawnEntity completes.
        TimerAction(period=3.0, actions=[
            Node(
                package="controller_manager", executable="spawner",
                arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
                output="screen",
            ),
            Node(
                package="controller_manager", executable="spawner",
                arguments=["gimbal_yaw_controller", "--controller-manager", "/controller_manager"],
                output="screen",
            ),
        ]),
        # Start the MID360 blind-sector sweep after the trajectory controller.
        TimerAction(period=5.0, actions=[
            Node(
                package="sentry_description",
                executable="gimbal_scan_sweep.py",
                output="screen",
                parameters=[{"use_sim_time": True}],
            ),
        ]),
    ])
