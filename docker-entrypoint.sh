#!/bin/bash
# Source ROS 2, the virtualenv and the workspace overlay before running the
# given command (defaults to "ros2 run tello tello", see the Dockerfile CMD).
set -e

source /opt/ros/jazzy/setup.bash
source "$VIRTUAL_ENV/bin/activate"
source "$WORKSPACE/install/setup.bash"

exec "$@"
