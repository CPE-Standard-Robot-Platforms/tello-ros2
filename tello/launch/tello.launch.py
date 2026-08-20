"""Launch the Tello driver, keyboard control, and visualization tools together."""

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    rviz_config = get_package_share_directory('tello') + '/rviz.rviz'

    nodes = [
        Node(
            package='tello',
            executable='tello',
            output='screen',
            name='tello',
            parameters=[
                {'connect_timeout': 10.0},
                {'tello_ip': '192.168.10.1'},
                {'tf_base': 'map'},
                {'tf_drone': 'drone'},
            ],
            remappings=[
                ('/image_raw', '/camera'),
            ],
            respawn=True,
        ),

        Node(
            package='tello_control',
            executable='tello_control',
            name='control',
            output='screen',
            respawn=False,
        ),

        Node(
            package='rqt_gui',
            executable='rqt_gui',
            output='screen',
            name='rqt',
            respawn=False,
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            output='screen',
            name='rviz2',
            respawn=True,
            arguments=['-d', rviz_config],
        ),

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            name='tf',
            arguments=['0', '0', '0', '0', '0', '0', '1', 'map', 'drone'],
            respawn=True,
        ),
    ]

    return LaunchDescription(nodes)
