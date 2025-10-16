from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

from mycobot_280jn.launch_utils import get_robot_description_parameter


def generate_launch_description():
    gzb_share = get_package_share_directory("gazebo_ros")
    pkg_share = get_package_share_directory("mycobot_280jn")

    world = LaunchConfiguration("world")
    entity_name = LaunchConfiguration("entity_name")
    rviz_config = LaunchConfiguration("rviz_config")
    use_rviz = LaunchConfiguration("use_rviz")
    goal_time = LaunchConfiguration("goal_time")
    min_period = LaunchConfiguration("min_publish_period")
    use_sim_time = LaunchConfiguration("use_sim_time")
    start_slider = LaunchConfiguration("start_slider")

    robot_description_content = get_robot_description_parameter()

    rviz_default_config = PathJoinSubstitution(
        [pkg_share, "config", "mycobot_jn.rviz"]
    )

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([gzb_share, "launch", "gazebo.launch.py"])]
        ),
        launch_arguments={"world": world}.items(),
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        name="robot_state_publisher",
        output="screen",
        parameters=[
            {"use_sim_time": use_sim_time},
            {"robot_description": robot_description_content},
        ],
    )

    spawn_entity = Node(
        package="gazebo_ros",
        executable="spawn_entity.py",
        arguments=["-entity", entity_name, "-topic", "robot_description"],
        output="screen",
    )

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
            "--controller-manager-timeout",
            "600",
        ],
        output="screen",
    )

    arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "arm_controller",
            "--controller-manager",
            "/controller_manager",
            "--controller-manager-timeout",
            "600",
        ],
        output="screen",
    )

    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="screen",
        arguments=["-d", rviz_config],
        parameters=[{"use_sim_time": use_sim_time}],
        condition=IfCondition(use_rviz),
    )

    slider_gui = Node(
        package="joint_state_publisher_gui",
        executable="joint_state_publisher_gui",
        name="joint_state_publisher_gui",
        parameters=[
            {"robot_description": robot_description_content},
            {"use_sim_time": use_sim_time},
        ],
        remappings=[("/joint_states", "/joint_targets")],
        condition=IfCondition(start_slider),
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
        condition=IfCondition(start_slider),
    )

    after_spawn_jsb = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_entity, on_exit=[joint_state_broadcaster_spawner]
        )
    )

    after_spawn_arm = RegisterEventHandler(
        OnProcessExit(target_action=spawn_entity, on_exit=[arm_controller_spawner])
    )

    rviz_after_jsb = RegisterEventHandler(
        OnProcessExit(target_action=joint_state_broadcaster_spawner, on_exit=[rviz_node])
    )

    slider_after_arm = RegisterEventHandler(
        OnProcessExit(
            target_action=arm_controller_spawner,
            on_exit=[slider_gui, trajectory_bridge],
        ),
        condition=IfCondition(start_slider),
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "world",
                default_value=PathJoinSubstitution(
                    [gzb_share, "worlds", "empty.world"]
                ),
                description="Gazebo world file to load",
            ),
            DeclareLaunchArgument(
                "entity_name",
                default_value="mycobot_280jn",
                description="Name of the entity to spawn in Gazebo",
            ),
            DeclareLaunchArgument(
                "rviz_config",
                default_value=rviz_default_config,
                description="Full path to the RViz config file to use",
            ),
            DeclareLaunchArgument(
                "use_rviz",
                default_value="true",
                description="Whether to start RViz alongside Gazebo",
            ),
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
            DeclareLaunchArgument(
                "start_slider",
                default_value="true",
                description="Start joint slider control once controllers are ready.",
            ),
            gazebo_launch,
            robot_state_publisher,
            spawn_entity,
            after_spawn_jsb,
            after_spawn_arm,
            rviz_after_jsb,
            slider_after_arm,
        ]
    )
