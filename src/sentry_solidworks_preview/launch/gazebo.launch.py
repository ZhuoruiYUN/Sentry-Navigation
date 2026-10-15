from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, SetEnvironmentVariable
from launch.substitutions import EnvironmentVariable


def generate_launch_description():
    share = Path(get_package_share_directory("sentry_solidworks_preview"))
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
            # Separate from the navigation simulator (11345) and older CAD
            # preview (11346).
            SetEnvironmentVariable(
                name="GAZEBO_MASTER_URI",
                value="http://127.0.0.1:11347",
            ),
            SetEnvironmentVariable(name="GAZEBO_MODEL_DATABASE_URI", value=""),
            ExecuteProcess(
                cmd=["gazebo", "--verbose", str(share / "worlds" / "sentry_cad_preview.world")],
                output="screen",
            ),
        ]
    )
