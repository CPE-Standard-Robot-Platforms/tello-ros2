# tello-ros2 container image.
#
# Mirrors the host virtualenv workflow documented in the README: a system ROS 2
# Jazzy install, plus a virtualenv holding the Python dependencies (djitellopy,
# opencv-python, av, numpy) and colcon itself. colcon has to live inside the
# virtualenv, otherwise the "ros2 run" executables it generates would be wired
# to the system Python and miss the drone dependencies.
#
# Build:
#   docker build -t tello-ros2 .
#
# Run (the Tello talks UDP to its own WiFi access point, hence --network host).
# The image ships fastdds_no_shm.xml, forcing plain UDPv4 for DDS: Fast DDS's
# default shared memory transport does not reliably reach processes on the
# host even with --ipc host (topics discover each other, but no message data
# ever arrives), so it is disabled instead of relying on IPC namespace sharing:
#   docker run --rm -it --network host tello-ros2
#
# Run the full stack (RViz, rqt) with a display forwarded from the host:
#   docker run --rm -it --network host -e DISPLAY="$DISPLAY" \
#       -v /tmp/.X11-unix:/tmp/.X11-unix tello-ros2 ros2 launch tello tello.launch.py

FROM ros:jazzy-ros-base

SHELL ["/bin/bash", "-c"]

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-venv \
    libopencv-dev \
    ros-jazzy-tf2-ros \
    ros-jazzy-rviz2 \
    ros-jazzy-rqt-gui \
    ros-jazzy-rqt-topic \
    ros-jazzy-camera-calibration \
    && rm -rf /var/lib/apt/lists/*

ENV WORKSPACE=/opt/ros2_ws
ENV VIRTUAL_ENV=/opt/tello_venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN python3 -m venv "$VIRTUAL_ENV"

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
    && pip install -r /tmp/requirements.txt

COPY . "$WORKSPACE/src/tello-ros2"

ENV FASTRTPS_DEFAULT_PROFILES_FILE="$WORKSPACE/src/tello-ros2/fastdds_no_shm.xml"

WORKDIR "$WORKSPACE"
RUN source /opt/ros/jazzy/setup.bash \
    && colcon build --symlink-install --packages-select tello tello_control tello_msg

COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["ros2", "run", "tello", "tello"]
