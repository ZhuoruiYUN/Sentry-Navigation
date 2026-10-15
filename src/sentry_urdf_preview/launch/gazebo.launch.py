from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from launch.substitutions import EnvironmentVariable


def generate_launch_description():
    share = Path(get_package_share_directory("sentry_urdf_preview"))
    return LaunchDescription(
        [
            SetEnvironmentVariable(
                name="GAZEBO_MODEL_PATH",
                value=[
                    str(share / "models"),
                    ":",
                    EnvironmentVariable("GAZEBO_MODEL_PATH", default_value=""),
                ],
            ),
            # Keep the CAD viewer independent from the navigation simulation,
            # which normally owns Gazebo Classic's default master port 11345.
            SetEnvironmentVariable(
                name="GAZEBO_MASTER_URI",
                value="http://127.0.0.1:11346",
            ),
            ExecuteProcess(
                cmd=["gazebo", "--verbose", str(share / "worlds" / "sentry_cad_preview.world")],
                output="screen",
            ),
        ]
    )
