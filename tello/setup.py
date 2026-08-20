from setuptools import setup

setup(
    name='tello',
    version='1.0.0',
    packages=['tello'],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/tello']),
        ('share/tello', ['package.xml', 'resource/ost.txt', 'resource/ost.yaml', 'rviz.rviz']),
        ('share/tello/launch', ['launch/tello.launch.py']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='tentone',
    maintainer_email='tentone@outlook.com',
    description='DJI Tello control package for ROS 2',
    license='MIT',
    entry_points={
        'console_scripts': [
            'tello = tello.node:main'
        ],
    },
)
