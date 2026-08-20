"""Camera calibration loading for the Tello driver node."""

import yaml


def load_camera_info(path):
    """Load a ROS camera calibration YAML file (as produced by camera_calibration) into a dict."""
    with open(path, 'r') as file:
        return yaml.safe_load(file)


def build_camera_info_msg(calibration):
    """Build a sensor_msgs/CameraInfo message from a loaded calibration dict."""
    from sensor_msgs.msg import CameraInfo

    msg = CameraInfo()
    msg.height = calibration['image_height']
    msg.width = calibration['image_width']
    msg.distortion_model = calibration['distortion_model']
    msg.d = calibration['distortion_coefficients']['data']
    msg.k = calibration['camera_matrix']['data']
    msg.r = calibration['rectification_matrix']['data']
    msg.p = calibration['projection_matrix']['data']
    return msg
