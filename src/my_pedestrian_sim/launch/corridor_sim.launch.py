import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, SetEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_my_pedestrian_sim = get_package_share_directory('my_pedestrian_sim')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    pkg_turtlebot3_gazebo = get_package_share_directory('turtlebot3_gazebo')

    # 使用するモデルを Burger に固定
    set_tb3_model = SetEnvironmentVariable('TURTLEBOT3_MODEL', 'burger')

    # ワールドファイルのパス
    world_file = os.path.join(pkg_my_pedestrian_sim, 'worlds', 'corridor.world')

    # Gazebo 起動
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gazebo.launch.py')
        ),
        launch_arguments={'world': world_file}.items()
    )

    # TurtleBot3 Burger の 3D モデル（URDF）を取得してスポーン
    urdf_file_name = 'turtlebot3_burger.urdf'
    urdf_path = os.path.join(pkg_turtlebot3_gazebo, 'urdf', urdf_file_name)
    with open(urdf_path, 'r') as infp:
        robot_desc = infp.read()

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_desc}]
    )

    spawn_turtlebot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'turtlebot3_burger',
            '-topic', 'robot_description',
            '-x', '2.0',
            '-y', '-2.0',
            '-z', '0.01'
        ],
        output='screen'
    )

    return LaunchDescription([
        set_tb3_model,
        gazebo,
        robot_state_publisher,
        spawn_turtlebot,
    ])
