#!/usr/bin/env python3
"""
Listen on /status_response for index 1 (status array) responses.
To request a status update, publish [0, 0, ...] to /status_command from the GUI
or use: ros2 topic pub --once /status_command std_msgs/Int16MultiArray "data: [0,0,...]"
"""

import rclpy
from std_msgs.msg import Int16MultiArray
import time

RESP_STATUS_ARRAY = 1


def main():
    rclpy.init()
    node = rclpy.create_node("nubi_status_monitor")

    def response_callback(msg):
        if not msg.data:
            return
        resp_index = msg.data[0]
        node.get_logger().info(f"Received response index: {resp_index}")
        if resp_index == RESP_STATUS_ARRAY:
            node.get_logger().info("-" * 57)
            node.get_logger().info("Status array received:")
            for i in range(20):
                err  = msg.data[i * 2 + 1]
                det  = msg.data[i * 2 + 2]
                node.get_logger().info(f"  Servo {i:2d}  statusError={err}  statusDetail={det}")
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
