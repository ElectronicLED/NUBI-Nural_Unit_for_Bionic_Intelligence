#!/usr/bin/env python3
"""
Listen on /status_response for index 5 (torque array) responses.
To request a torque update, publish [3, 0, ...] to /status_command from the GUI
or use: ros2 topic pub --once /status_command std_msgs/Int16MultiArray "data: [3,0,...]"
"""

import rclpy
from std_msgs.msg import Int16MultiArray
import time

RESP_TORQUE_ARRAY = 5


def main():
    rclpy.init()
    node = rclpy.create_node("nubi_torque_monitor")

    def response_callback(msg):
        if not msg.data:
            return
        resp_index = msg.data[0]
        node.get_logger().info(f"Received response index: {resp_index}")
        if resp_index == RESP_TORQUE_ARRAY:
            node.get_logger().info("-" * 57)
            node.get_logger().info("Torque array received:")
            for i in range(20):
                tq = msg.data[i + 1]
                state = "ON" if tq == 1 else ("OFF" if tq == 0 else f"unclear({tq})")
                node.get_logger().info(f"  Servo {i:2d}  Torque {state}")
            node.get_logger().info("-" * 57)
            time.sleep(0.5)

    subscriber = node.create_subscription(Int16MultiArray, "status_response", response_callback, 10)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
