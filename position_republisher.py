#!/usr/bin/env python3
"""
position_republisher.py

Simulates robot motion for testing purposes when the physical robot is absent.
Subscribes to command topics and republishes them as feedback topics,
assuming commanded positions are immediately reached.

Topics:
  Subscribed:  /upperbody_command  (std_msgs/Int16MultiArray)
               /legs_command       (std_msgs/Int16MultiArray)
  Published:   /upperbody_feedback (std_msgs/Int16MultiArray)
               /legs_feedback      (std_msgs/Int16MultiArray)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int16MultiArray


class PositionRepublisher(Node):
    def __init__(self):
        super().__init__('position_republisher')

        self.upperbody_feedback_pub = self.create_publisher(
            Int16MultiArray, 'upperbody_feedback', 10
        )
        self.legs_feedback_pub = self.create_publisher(
            Int16MultiArray, 'legs_feedback', 10
        )

        self.create_subscription(
            Int16MultiArray,
            'upperbody_command',
            self._upperbody_cmd_callback,
            10,
        )
        self.create_subscription(
            Int16MultiArray,
            'legs_command',
            self._legs_cmd_callback,
            10,
        )

        self.get_logger().info(
            'PositionRepublisher started — forwarding commands to feedback topics.'
        )

        # Publish zero positions immediately on startup
        zero_upper = Int16MultiArray()
        zero_upper.data = [0] * 7
        self.upperbody_feedback_pub.publish(zero_upper)

        zero_legs = Int16MultiArray()
        zero_legs.data = [0] * 12
        self.legs_feedback_pub.publish(zero_legs)

        self.get_logger().info('Published zero positions on startup.')

    def _upperbody_cmd_callback(self, msg: Int16MultiArray):
        self.upperbody_feedback_pub.publish(msg)
        self.get_logger().debug(f'upperbody_feedback: {list(msg.data)}')

    def _legs_cmd_callback(self, msg: Int16MultiArray):
        self.legs_feedback_pub.publish(msg)
        self.get_logger().debug(f'legs_feedback: {list(msg.data)}')


def main(args=None):
    rclpy.init(args=args)
    node = PositionRepublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
