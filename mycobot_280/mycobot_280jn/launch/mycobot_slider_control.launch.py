from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from mycobot_280jn.launch_utils import get_robot_description_parameter

def generate_launch_description():
    goal_time = LaunchConfiguration("goal_time")
    min_period = LaunchConfiguration("min_publish_period")
    use_sim_time = LaunchConfiguration("use_sim_time")

    robot_description_content = get_robot_description_parameter()

    slider_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        parameters=[
            {"robot_description": robot_description_content},
            {"use_sim_time": use_sim_time},
        ],
        remappings=[("/joint_states", "/joint_targets")],
    )

    trajectory_bridge = Node(
        package="mycobot_280jn",
        executable="joint_slider_trajectory",
        name="joint_slider_trajectory",
        parameters=[
            {"use_sim_time": use_sim_time},
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
            DeclareLaunchArgument(
                "use_sim_time",
                default_value="true",
                description="Whether nodes should use simulated time.",
            ),
            slider_gui,
            trajectory_bridge,
        ]
    )
