"""Entry point for the tello driver node."""

import rclpy

from tello.tello_node import TelloNode


def main(args=None):
    rclpy.init(args=args)

    node = TelloNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.shutdown()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
