from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command 
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    pkg_share = get_package_share_directory("mycobot_280jn")
    description_share = get_package_share_directory("mycobot_description")

    goal_time = LaunchConfiguration("goal_time")
    min_period = LaunchConfiguration("min_publish_period")

    ros2_control_config = PathJoinSubstitution(
        [pkg_share, "config", "mycobot_280jn_ros2_control.yaml"]
    )

    gazebo_xacro = PathJoinSubstitution(
        [description_share, "urdf", "mycobot_280_jn", "mycobot_280_jn_gazebo_refactored.urdf.xacro"]
    )

    robot_description_content = ParameterValue(
        Command(
            [
                "xacro ",
                gazebo_xacro,
                " ros2_control_config:=",
                ros2_control_config,
            ]
        ),
        value_type=str,
    )

    slider_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        parameters=[
            {"robot_description": robot_description_content},
            {"use_sim_time": True},
        ],
        remappings=[("/joint_states", "/joint_targets")],
    )

    trajectory_bridge = Node(
        package="mycobot_280jn",
        executable="joint_slider_trajectory",
        name="joint_slider_trajectory",
        parameters=[
            {"use_sim_time": True},
            {"goal_time": goal_time},
            {"min_publish_period": min_period},
            {"joint_state_topic": "/joint_targets"},
            {"trajectory_topic": "/arm_controller/joint_trajectory"},
        ],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "goal_time",
                default_value="0.5",
                description="Seconds for the controller to reach each target point.",
            ),
            DeclareLaunchArgument(
                "min_publish_period",
                default_value="0.05",
                description="Minimum period between trajectory commands.",
            ),
            slider_gui,
            trajectory_bridge,
        ]
    )
