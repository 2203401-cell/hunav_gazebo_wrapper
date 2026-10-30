from os import environ, pathsep

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    ExecuteProcess,
    RegisterEventHandler,
    SetEnvironmentVariable,
    Shutdown,
    TimerAction,
    LogInfo,
)
from launch.event_handlers import OnProcessStart
from launch.substitutions import (
    LaunchConfiguration,
    PathJoinSubstitution,
)
from launch.conditions import IfCondition
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.actions import IncludeLaunchDescription


def generate_launch_description():
    pkg_share = get_package_share_directory('hunav_gazebo_wrapper')
    world_dir = pathsep.join([
        pkg_share + '/worlds/corridor_experiment',
        environ.get('GAZEBO_MODEL_PATH', ''),
    ]).rstrip(pathsep)

    base_world = PathJoinSubstitution([
        FindPackageShare('hunav_gazebo_wrapper'),
        'worlds', 'corridor_experiment', 'corridor.world'
    ])

    scenario = PathJoinSubstitution([
        FindPackageShare('hunav_gazebo_wrapper'),
        'scenarios', 'agents_corridor_1.yaml'
    ])

    generator = Node(
        package='hunav_gazebo_wrapper',
        executable='hunav_gazebo_world_generator',
        output='screen',
        parameters=[{
            'base_world': base_world,
            'use_gazebo_obs': True,
            'update_rate': 1000.0,
            'robot_name': 'turtlebot3_burger',
            'global_frame_to_publish': 'map',
            'use_navgoal_to_start': False,
            'navgoal_topic': 'hunav_goal_pose',
            'ignore_models': 'ground_plane sun',
        }],
    )

    loader = Node(
        package='hunav_agent_manager',
        executable='hunav_loader',
        output='screen',
        parameters=[scenario],
    )

    manager = Node(
        package='hunav_agent_manager',
        executable='hunav_agent_manager',
        name='hunav_agent_manager',
        output='screen',
        parameters=[{'use_sim_time': True}],
    )

    gazebo_env = [
        SetEnvironmentVariable(
            name='GAZEBO_MODEL_PATH',
            value=[
                world_dir,
                ':',
                environ.get('GAZEBO_MODEL_PATH', ''),
            ],
        ),
        SetEnvironmentVariable(
            name='GAZEBO_RESOURCE_PATH',
            value=[
                '/usr/share/gazebo-11:',
                environ.get('GAZEBO_RESOURCE_PATH', ''),
                ':',
                pkg_share,
            ],
        ),
    ]

    generated_world = PathJoinSubstitution([
        FindPackageShare('hunav_gazebo_wrapper'),
        'worlds', 'corridor_experiment', 'generatedWorld.world'
    ])

    gzserver = ExecuteProcess(
        cmd=[
            'gzserver', '--verbose',
            generated_world,
            '-s', 'libgazebo_ros_init.so',
            '-s', 'libgazebo_ros_factory.so',
        ],
        output='screen',
        shell=False,
        on_exit=Shutdown(),
    )

    gzclient = ExecuteProcess(
        cmd=['gzclient', '--verbose'],
        output='screen',
        shell=False,
        on_exit=Shutdown(),
    )

    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        output='screen',
        arguments=[
            '-entity', 'turtlebot3_burger',
            '-file', PathJoinSubstitution([
                FindPackageShare('turtlebot3_gazebo'),
                'models', 'turtlebot3_burger', 'model.sdf'
            ]),
            '-x', '0.0',
            '-y', '0.0',
            '-z', '0.1',
            '-Y', '0.0',
        ],
    )

    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare('turtlebot3_gazebo'),
                'launch', 'robot_state_publisher.launch.py'
            ])
        ]),
        launch_arguments={'use_sim_time': 'true'}.items(),
        condition=IfCondition(LaunchConfiguration('start_robot')),
    )

    start_robot = LaunchConfiguration('start_robot')

    return LaunchDescription([
        DeclareLaunchArgument(
            'start_robot',
            default_value='false',
            description='Spawn TurtleBot3 for the experiment',
        ),
        *gazebo_env,
        loader,
        RegisterEventHandler(
            OnProcessStart(
                target_action=loader,
                on_start=[
                    LogInfo(msg='HuNav loader started; generating isolated corridor world in 2 seconds'),
                    TimerAction(period=2.0, actions=[generator]),
                ],
            )
        ),
        manager,
        RegisterEventHandler(
            OnProcessStart(
                target_action=generator,
                on_start=[
                    LogInfo(msg='World generator started; starting Gazebo in 2 seconds'),
                    TimerAction(period=2.0, actions=[gzserver, gzclient]),
                ],
            )
        ),
        robot_state_publisher,
        RegisterEventHandler(
            OnProcessStart(
                target_action=gzserver,
                on_start=[
                    TimerAction(period=5.0, actions=[spawn_robot]),
                ],
            ),
            condition=IfCondition(start_robot),
        ),
    ])
