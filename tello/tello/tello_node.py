"""ROS 2 driver node for the DJI Tello drone."""

import threading
import time

import rclpy
import tf2_ros
from ament_index_python.packages import get_package_share_directory
from djitellopy import Tello
from geometry_msgs.msg import Twist, TransformStamped
from nav_msgs.msg import Odometry
from rclpy.node import Node
from sensor_msgs.msg import Image, Imu, BatteryState, Temperature, CameraInfo
from std_msgs.msg import Empty, String

from tello.camera import build_camera_info_msg, load_camera_info
from tello.conversions import euler_to_quaternion, frame_to_image_msg
from tello_msg.msg import TelloStatus, TelloID, TelloWifiConfig


class TelloNode(Node):
    """Publishes telemetry and camera data from a DJI Tello drone and exposes control topics."""

    def __init__(self):
        super().__init__('tello')

        self.declare_parameter('connect_timeout', 10.0)
        self.declare_parameter('tello_ip', '192.168.10.1')
        self.declare_parameter('tf_base', 'map')
        self.declare_parameter('tf_drone', 'drone')
        self.declare_parameter('tf_pub', False)
        self.declare_parameter('camera_info_file', '')

        self.connect_timeout = float(self.get_parameter('connect_timeout').value)
        self.tello_ip = str(self.get_parameter('tello_ip').value)
        self.tf_base = str(self.get_parameter('tf_base').value)
        self.tf_drone = str(self.get_parameter('tf_drone').value)
        self.tf_pub = bool(self.get_parameter('tf_pub').value)
        self.camera_info_file = str(self.get_parameter('camera_info_file').value)

        if not self.camera_info_file:
            share_directory = get_package_share_directory('tello')
            self.camera_info_file = share_directory + '/ost.yaml'

        self.camera_info = load_camera_info(self.camera_info_file)

        Tello.TELLO_IP = self.tello_ip
        Tello.RESPONSE_TIMEOUT = int(self.connect_timeout)

        self.get_logger().info('Tello: Connecting to drone')
        self.tello = Tello()
        self.tello.connect()
        self.get_logger().info('Tello: Connected to drone')

        self._setup_publishers()
        self._setup_subscribers()

        self._threads = [
            self._start_video_capture(),
            self._start_status_loop(),
            self._start_odom_loop(),
        ]

        self.get_logger().info('Tello: Driver node ready')

    def _setup_publishers(self):
        self.pub_image_raw = self.create_publisher(Image, 'image_raw', 1)
        self.pub_camera_info = self.create_publisher(CameraInfo, 'camera_info', 1)
        self.pub_status = self.create_publisher(TelloStatus, 'status', 1)
        self.pub_id = self.create_publisher(TelloID, 'id', 1)
        self.pub_imu = self.create_publisher(Imu, 'imu', 1)
        self.pub_battery = self.create_publisher(BatteryState, 'battery', 1)
        self.pub_temperature = self.create_publisher(Temperature, 'temperature', 1)
        self.pub_odom = self.create_publisher(Odometry, 'odom', 1)

        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self) if self.tf_pub else None

    def _setup_subscribers(self):
        self.create_subscription(Empty, 'emergency', self._on_emergency, 1)
        self.create_subscription(Empty, 'takeoff', self._on_takeoff, 1)
        self.create_subscription(Empty, 'land', self._on_land, 1)
        self.create_subscription(Twist, 'control', self._on_control, 1)
        self.create_subscription(String, 'flip', self._on_flip, 1)
        self.create_subscription(TelloWifiConfig, 'wifi_config', self._on_wifi_config, 1)

    def _get_orientation_quaternion(self):
        deg_to_rad = 3.141592653589793 / 180.0
        return euler_to_quaternion(
            self.tello.get_yaw() * deg_to_rad,
            self.tello.get_pitch() * deg_to_rad,
            self.tello.get_roll() * deg_to_rad,
        )

    def _run_loop(self, name, rate, body):
        """Run body() in a background loop, logging and continuing on error instead of dying."""
        def loop():
            while rclpy.ok():
                try:
                    body()
                except Exception as error:  # noqa: BLE001 - keep the loop alive on drone errors
                    self.get_logger().warn(f'Tello: {name} loop error: {error}')
                time.sleep(rate)

        thread = threading.Thread(target=loop, name=name, daemon=True)
        thread.start()
        return thread

    def _start_odom_loop(self, rate=1.0 / 10.0):
        def body():
            if self.tf_pub and self.tf_broadcaster is not None:
                t = TransformStamped()
                t.header.stamp = self.get_clock().now().to_msg()
                t.header.frame_id = self.tf_base
                t.child_frame_id = self.tf_drone
                t.transform.translation.z = self.tello.get_barometer() / 100.0
                self.tf_broadcaster.sendTransform(t)

            if self.pub_imu.get_subscription_count() > 0:
                q = self._get_orientation_quaternion()

                msg = Imu()
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.header.frame_id = self.tf_drone
                msg.linear_acceleration.x = self.tello.get_acceleration_x() / 100.0
                msg.linear_acceleration.y = self.tello.get_acceleration_y() / 100.0
                msg.linear_acceleration.z = self.tello.get_acceleration_z() / 100.0
                msg.orientation.x = q[0]
                msg.orientation.y = q[1]
                msg.orientation.z = q[2]
                msg.orientation.w = q[3]
                self.pub_imu.publish(msg)

            if self.pub_odom.get_subscription_count() > 0:
                q = self._get_orientation_quaternion()

                msg = Odometry()
                msg.header.stamp = self.get_clock().now().to_msg()
                msg.header.frame_id = self.tf_base
                msg.pose.pose.orientation.x = q[0]
                msg.pose.pose.orientation.y = q[1]
                msg.pose.pose.orientation.z = q[2]
                msg.pose.pose.orientation.w = q[3]
                msg.twist.twist.linear.x = float(self.tello.get_speed_x()) / 100.0
                msg.twist.twist.linear.y = float(self.tello.get_speed_y()) / 100.0
                msg.twist.twist.linear.z = float(self.tello.get_speed_z()) / 100.0
                self.pub_odom.publish(msg)

        return self._run_loop('odom', rate, body)

    def _start_status_loop(self, rate=1.0 / 2.0):
        def body():
            if self.pub_battery.get_subscription_count() > 0:
                msg = BatteryState()
                msg.header.frame_id = self.tf_drone
                msg.percentage = float(self.tello.get_battery())
                msg.voltage = 3.8
                msg.design_capacity = 1.1
                msg.present = True
                msg.power_supply_technology = BatteryState.POWER_SUPPLY_TECHNOLOGY_LION
                msg.power_supply_status = BatteryState.POWER_SUPPLY_STATUS_DISCHARGING
                self.pub_battery.publish(msg)

            if self.pub_temperature.get_subscription_count() > 0:
                msg = Temperature()
                msg.header.frame_id = self.tf_drone
                msg.temperature = self.tello.get_temperature()
                msg.variance = 0.0
                self.pub_temperature.publish(msg)

            if self.pub_status.get_subscription_count() > 0:
                msg = TelloStatus()
                msg.acceleration.x = self.tello.get_acceleration_x()
                msg.acceleration.y = self.tello.get_acceleration_y()
                msg.acceleration.z = self.tello.get_acceleration_z()

                msg.speed.x = float(self.tello.get_speed_x())
                msg.speed.y = float(self.tello.get_speed_y())
                msg.speed.z = float(self.tello.get_speed_z())

                msg.pitch = self.tello.get_pitch()
                msg.roll = self.tello.get_roll()
                msg.yaw = self.tello.get_yaw()

                msg.barometer = int(self.tello.get_barometer())
                msg.distance_tof = self.tello.get_distance_tof()

                msg.flight_time = self.tello.get_flight_time()

                msg.battery = self.tello.get_battery()

                msg.highest_temperature = self.tello.get_highest_temperature()
                msg.lowest_temperature = self.tello.get_lowest_temperature()
                msg.temperature = self.tello.get_temperature()

                msg.wifi_snr = str(self.tello.query_wifi_signal_noise_ratio())

                self.pub_status.publish(msg)

            if self.pub_id.get_subscription_count() > 0:
                msg = TelloID()
                msg.sdk_version = self.tello.query_sdk_version()
                msg.serial_number = self.tello.query_serial_number()
                self.pub_id.publish(msg)

            if self.pub_camera_info.get_subscription_count() > 0:
                self.pub_camera_info.publish(build_camera_info_msg(self.camera_info))

        return self._run_loop('status', rate, body)

    def _start_video_capture(self, rate=1.0 / 30.0):
        self.tello.streamon()

        def body():
            frame_read = self.tello.get_frame_read()
            frame = frame_read.frame
            if frame is None:
                return

            msg = frame_to_image_msg(frame, 'bgr8')
            msg.header.frame_id = self.tf_drone
            self.pub_image_raw.publish(msg)

        return self._run_loop('video', rate, body)

    def shutdown(self):
        """Land safely if needed and release the connection to the drone."""
        try:
            self.tello.end()
        except Exception as error:  # noqa: BLE001 - best effort on shutdown
            self.get_logger().warn(f'Tello: error while shutting down: {error}')

    def _on_emergency(self, msg):
        self.tello.emergency()

    def _on_takeoff(self, msg):
        self.tello.takeoff()

    def _on_land(self, msg):
        self.tello.land()

    def _on_control(self, msg):
        self.tello.send_rc_control(
            int(msg.linear.x), int(msg.linear.y), int(msg.linear.z), int(msg.angular.z))

    def _on_wifi_config(self, msg):
        self.tello.set_wifi_credentials(msg.ssid, msg.password)

    def _on_flip(self, msg):
        self.tello.flip(msg.data)
