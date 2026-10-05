"""Entry point for the tello driver node."""

import rclpy
from rclpy.executors import MultiThreadedExecutor

from tello.tello_node import TelloNode


def main(args=None):
    rclpy.init(args=args)

    node = TelloNode()
    # Multi-threaded so emergency/control keep running while a maneuver callback is blocked.
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
