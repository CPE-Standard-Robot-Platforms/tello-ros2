#!/bin/bash
# Install the system dependencies for tello-ros2 on Ubuntu 24.04 with ROS 2 Jazzy
# already installed. Python dependencies are handled separately by
# scripts/setup_venv.sh, inside a virtualenv.

set -euo pipefail

if (( EUID != 0 )); then
    echo " - Please run as root"
    exit 1
fi

echo " - Installing build tools"
apt update
apt install -y build-essential python3-venv python3-colcon-common-extensions

echo " - Installing ROS 2 dependencies"
apt install -y \
    ros-jazzy-tf2-ros \
    ros-jazzy-rviz2 \
    ros-jazzy-rqt-gui \
    ros-jazzy-rqt-topic \
    ros-jazzy-camera-calibration

echo " - System dependencies installed"
echo " - Next: run ./scripts/setup_venv.sh, activate the virtualenv, then ./scripts/build.sh"
