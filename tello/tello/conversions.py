"""Rotation and image conversion helpers used by the Tello driver node."""

import math

import numpy


def euler_to_quaternion(yaw, pitch, roll):
    """Convert an intrinsic yaw/pitch/roll rotation (radians) to a quaternion [x, y, z, w]."""
    qx = math.sin(roll / 2) * math.cos(pitch / 2) * math.cos(yaw / 2) \
        - math.cos(roll / 2) * math.sin(pitch / 2) * math.sin(yaw / 2)
    qy = math.cos(roll / 2) * math.sin(pitch / 2) * math.cos(yaw / 2) \
        + math.sin(roll / 2) * math.cos(pitch / 2) * math.sin(yaw / 2)
    qz = math.cos(roll / 2) * math.cos(pitch / 2) * math.sin(yaw / 2) \
        - math.sin(roll / 2) * math.sin(pitch / 2) * math.cos(yaw / 2)
    qw = math.cos(roll / 2) * math.cos(pitch / 2) * math.cos(yaw / 2) \
        + math.sin(roll / 2) * math.sin(pitch / 2) * math.sin(yaw / 2)
    return [qx, qy, qz, qw]


def quaternion_to_euler(x, y, z, w):
    """Convert a quaternion to a yaw/pitch/roll rotation (radians)."""
    t0 = 2.0 * (w * x + y * z)
    t1 = 1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(t0, t1)

    t2 = max(-1.0, min(1.0, 2.0 * (w * y - z * x)))
    pitch = math.asin(t2)

    t3 = 2.0 * (w * z + x * y)
    t4 = 1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(t3, t4)

    return [yaw, pitch, roll]


def frame_to_image_msg(frame, encoding='bgr8'):
    """Build a sensor_msgs/Image from a HxWx3 uint8 numpy array without depending on cv_bridge.

    cv_bridge ships as a compiled apt package tied to the system NumPy ABI, which conflicts
    with pip-installed NumPy inside a virtualenv. Building the message by hand avoids that.
    """
    from sensor_msgs.msg import Image

    array = numpy.ascontiguousarray(frame, dtype=numpy.uint8)
    height, width, channels = array.shape

    msg = Image()
    msg.height = height
    msg.width = width
    msg.encoding = encoding
    msg.is_bigendian = 0
    msg.step = width * channels
    msg.data = array.tobytes()
    return msg
