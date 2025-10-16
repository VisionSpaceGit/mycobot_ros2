from launch.substitutions import Command, PathJoinSubstitution
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory


def get_robot_description_parameter() -> ParameterValue:
    """Return shared robot_description ParameterValue for mycobot_280jn."""
    pkg_share = get_package_share_directory("mycobot_280jn")
    description_share = get_package_share_directory("mycobot_description")

    ros2_control_config = PathJoinSubstitution(
        [pkg_share, "config", "mycobot_280jn_ros2_control.yaml"]
    )

    gazebo_xacro = PathJoinSubstitution(
        [
            description_share,
            "urdf",
            "mycobot_280_jn",
            "mycobot_280_jn_gazebo_refactored.urdf.xacro",
        ]
    )

    return ParameterValue(
        Command(
            [
                "xacro",
                " ",
                gazebo_xacro,
                " ",
                "ros2_control_config:=",
                ros2_control_config,
            ]
        ),
        value_type=str,
    )
