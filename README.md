# DJI Tello ROS2

- [DJI Tello](https://www.ryzerobotics.com/tello) driver for ROS 2 based on [DJITelloPy](https://github.com/damiafuentes/DJITelloPy), using the [official SDK](https://github.com/dji-sdk/Tello-Python) for the drone.
- Targets ROS 2 Jazzy on Ubuntu 24.04, and is meant to be built inside a Python virtualenv (see Quickstart below).
- Can control multiple drones, either using the swarm functionality (only for [Tello EDU](https://www.ryzerobotics.com/tello-edu)) or by running one node per drone on separate WLANs with regular [Tello](https://www.ryzerobotics.com/tello) drones.
- It is recommended to update the Tello firmware to the latest version available.

<img src="readme/ros.jpg" width="380"><img src="readme/drone_b.jpg" width="380">

## Packages

| Package         | Type          | Description                                                                 |
| ---------------- | ------------- | ---------------------------------------------------------------------------- |
| `tello`         | ament_python | Driver node: connects to the drone, publishes telemetry and camera images, exposes control topics. |
| `tello_msg`     | ament_cmake  | Custom messages: `TelloStatus`, `TelloID`, `TelloWifiConfig`.                |
| `tello_control` | ament_cmake  | Sample keyboard teleop node (OpenCV window driven).                          |

## Quickstart (virtualenv)

This project keeps its Python dependencies (`djitellopy`, `opencv-python`, `av`, `numpy`, ...) in a virtualenv rather than mixed into the system Python, so it does not depend on whatever versions happen to be packaged for ROS 2 Jazzy. `colcon` itself must be installed inside that same virtualenv: colcon embeds its own interpreter path into the executables it generates, so running colcon from outside the virtualenv makes `ros2 run` launch nodes with the system Python instead, missing the drone dependencies entirely.

Clone this repository as `<ros2_ws>/src/tello-ros2` (with `<ros2_ws>` any ROS 2 workspace directory of your choice), then:

```bash
# System dependencies (build tools, RViz, rqt, ...), once per machine
sudo ./scripts/install.sh

# Python virtualenv with djitellopy, opencv-python, av, numpy and colcon
./scripts/setup_venv.sh
source .venv/bin/activate

# Build and run
./scripts/build.sh
./scripts/run.sh
```

`scripts/build.sh` runs `colcon build --symlink-install --packages-select tello tello_control tello_msg` from the workspace root. `scripts/run.sh` sources the workspace and launches `tello.launch.py` (driver, keyboard control, rqt, rviz2 and a static TF publisher).

To iterate manually instead of using the scripts:

```bash
source .venv/bin/activate
cd <ros2_ws>
colcon build --symlink-install --packages-select tello tello_control tello_msg
source install/setup.bash
ros2 launch tello tello.launch.py
```

## Docker

A `Dockerfile` is provided to run the driver without installing ROS 2 or a virtualenv on the host. See the [Docker section](#running-with-docker) below.

## Topics published by `tello`

Published topics are only computed and sent when something is subscribed to them.

| Topic        | Type                            | Description                                                   | Frequency |
| ------------ | -------------------------------- | --------------------------------------------------------------- | --------- |
| /image_raw   | sensor_msgs/Image               | Image from the Tello camera                                    | 30 Hz     |
| /camera_info | sensor_msgs/CameraInfo          | Camera calibration (size, distortion, etc)                     | 2 Hz      |
| /status      | tello_msg/TelloStatus           | Drone status (wifi strength, battery, temperature, etc)        | 2 Hz      |
| /id          | tello_msg/TelloID               | Drone identification (serial number, SDK version)              | 2 Hz      |
| /imu         | sensor_msgs/Imu                 | IMU data from the drone                                        | 10 Hz     |
| /battery     | sensor_msgs/BatteryState        | Battery status                                                  | 2 Hz      |
| /temperature | sensor_msgs/Temperature         | Drone temperature                                               | 2 Hz      |
| /odom        | nav_msgs/Odometry               | Odometry (orientation and speed only)                          | 10 Hz     |
| /tf          | geometry_msgs/TransformStamped  | Transform from `tf_base` to `tf_drone`, only if `tf_pub` is set | 10 Hz     |

## Topics subscribed by `tello`

These can be renamed in the launch file with `remappings`.

| Topic        | Type                       | Description                                                                                                                                              |
| ------------ | --------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| /emergency   | std_msgs/Empty             | Instantly cuts the motors, even mid flight. Safety use only.                                                                                              |
| /takeoff     | std_msgs/Empty             | Takeoff. Make sure the drone has room to take off safely first.                                                                                           |
| /land        | std_msgs/Empty             | Land the drone.                                                                                                                                            |
| /control     | geometry_msgs/Twist        | Analog control. Linear values range from -100 to 100 for x, y, z movement. Angular rotation is applied on z. Coordinates are relative to the drone facing. |
| /flip        | std_msgs/String             | Flip in a direction: `r` right, `l` left, `f` forward, `b` backward.                                                                                       |
| /wifi_config | tello_msg/TelloWifiConfig  | Set the wifi credentials the drone should use. The drone restarts after the change.                                                                       |

## Parameters

| Name              | Type    | Description                                                          | Default          |
| ------------------ | ------- | ----------------------------------------------------------------------- | ------------------ |
| connect_timeout   | float   | Seconds to wait for the drone to respond before failing a command.   | 10.0              |
| tello_ip          | string  | IP of the drone. Use different values to run several drones at once. | '192.168.10.1'    |
| tf_base           | string  | Base frame used when publishing TF and odometry data.                | 'map'             |
| tf_drone          | string  | Drone frame used when publishing TF and sensor data.                 | 'drone'           |
| tf_pub            | boolean | Publish a TF from `tf_base` to `tf_drone`.                            | False             |
| camera_info_file  | string  | Path to a camera calibration YAML file. Empty uses the bundled sample.| ''                |

## Keyboard control (`tello_control`)

`T` takeoff, `L` land, `F` flip forward, `E` emergency stop, `WASD` and arrow keys to move.

## Camera calibration

A sample calibration file, captured on the maintainers' test drone, is bundled at `tello/resource/ost.yaml`. Every drone is slightly different, so calibrate your own for anything vision-sensitive (monocular SLAM, AR markers, ...):

```bash
ros2 run camera_calibration cameracalibrator --size 7x9 --square 0.16 image:=/image_raw camera:=/camera_info
```

Take as many frames as possible and measure your checkerboard accurately. A `calibrationdata.tar.gz` is produced in `/tmp` once done; convert it to the `ost.yaml` format expected by `camera_info_file`.

<img src="readme/calibration.jpg" width="380">

## Overheating

The motor drivers overheat after a while when the drone is powered on but not flying. Removing the plastic cover over the heat spreader (pictured) helps a lot; placing the drone on a laptop cooler or an old computer fan also helps if you are running it on a bench for a while.

<img src="readme/drone_a.jpg" width="380">

## Visual SLAM (optional, advanced)

The drone's camera and IMU can be used for visual SLAM with [ORB-SLAM2](https://github.com/raulmur/ORB_SLAM2). This is not part of the default build (`slam/src/orbslam2` carries a `COLCON_IGNORE` marker) since it needs the external `ORB_SLAM2` library, which is not packaged for Jazzy. See [SLAM.md](SLAM.md) and `scripts/orbslam.sh` for the manual build steps, and remove the `COLCON_IGNORE` marker once the dependency is installed.

## Running with Docker

Build the image from the repository root:

```bash
docker build -t tello-ros2 .
```

Run it. The Tello communicates over a UDP link on the drone's own WiFi network, so the container needs to share the host's network stack:

```bash
docker run --rm -it --network host tello-ros2
```

By default the container launches `ros2 run tello tello`. Override the command to run something else, for example the full launch file with a display forwarded from the host:

```bash
docker run --rm -it --network host -e DISPLAY="$DISPLAY" -v /tmp/.X11-unix:/tmp/.X11-unix \
    tello-ros2 ros2 launch tello tello.launch.py
```

See the comments in the `Dockerfile` for details on how the image is built (system ROS 2 install plus an internal virtualenv, same approach as the host Quickstart above).
