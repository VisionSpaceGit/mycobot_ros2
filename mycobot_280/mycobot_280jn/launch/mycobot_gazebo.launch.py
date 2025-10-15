from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
from launch.event_handlers import OnProcessExit  

def generate_launch_description():
    pkg_share = get_package_share_directory('mycobot_280jn')
    dsc_share = get_package_share_directory('mycobot_description')

    world = LaunchConfiguration('world')
    entity_name = LaunchConfiguration('entity_name') 
    rviz_config = LaunchConfiguration('rviz_config')

    ros2_control_config = PathJoinSubstitution(
        [pkg_share, 'config', 'mycobot_280jn_ros2_control.yaml']
    )

    gazebo_xacro = PathJoinSubstitution(
        [dsc_share, 'urdf', 'mycobot_280_jn', 'mycobot_280_jn_gazebo.urdf.xacro']
    )

    robot_description_content = ParameterValue(
        Command([
            'xacro', ' ',
            gazebo_xacro, ' ',
            'ros2_control_config:=', ros2_control_config
        ]),
        value_type=str
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{
            'use_sim_time': True,
            'robot_description': robot_description_content
        }]
    )

    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            [PathJoinSubstitution([get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py'])]
        ),
        launch_arguments={'world': world}.items()
    )

    spawn_entity = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', entity_name,
            '-topic', 'robot_description'
        ],
        output='screen'
    )

    # 모델 삽입이 끝난 뒤 스포너 실행 (OnProcessExit)
    after_spawn_jsb = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_entity,
            on_exit=[Node(
                package='controller_manager',
                executable='spawner',
                arguments=[
                    'joint_state_broadcaster',
                    '--controller-manager', 'controller_manager',
                    # PathJoinSubstitution(['/', entity_name, 'controller_manager']),
                    '--controller-manager-timeout', '600'
                ],
                output='screen'
            )]
        )
    )

    after_spawn_arm = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_entity,
            on_exit=[Node(
                package='controller_manager',
                executable='spawner',
                arguments=[
                    'arm_controller', 
                    '--controller-manager', 'controller_manager',
                    # PathJoinSubstitution(['/', entity_name, 'controller_manager']),
                    '--controller-manager-timeout', '600'
                ],
                output='screen'
            )]
        )
    )

    rviz_default_config = PathJoinSubstitution(
        [pkg_share, 'config', 'mycobot_jn.rviz']
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'world',
            default_value=PathJoinSubstitution(
                [get_package_share_directory('gazebo_ros'), 'worlds', 'empty.world']
            ),
            description='Gazebo world file to load'
        ),
        DeclareLaunchArgument(
            'entity_name',
            default_value='mycobot_280jn',
            description='Name of the entity to spawn in Gazebo'
        ),
        DeclareLaunchArgument(
            'rviz_config',
            default_value=rviz_default_config,
            description='Full path to the RViz config file to use'
        ),
        robot_state_publisher,
        gazebo_launch,
        spawn_entity,
        after_spawn_jsb,
        after_spawn_arm,
    ])
