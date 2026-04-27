#!usr/bin/env python3 

import rclpy
from std_msgs.msg import UInt8MultiArray
import time


def main():
    rclpy.init()
    node = rclpy.create_node("torque_feedback_node")

    def status_callback(msg):
        node.get_logger().info(f"---------------------------------------------------------")
        node.get_logger().info(f"The torque status of each servo is:")
        for i in range(20):
            node.get_logger().info(f"Servo {i}")
            if msg.data[i] == 1:
                node.get_logger().info(f"Torque ON")
            elif msg.data[i] == 0:
                node.get_logger().info(f"Torque OFF")
            else:
                node.get_logger().info(f"unclear")
        node.get_logger().info(f"---------------------------------------------------------")
        node.get_logger().info(f"Done")
        time.sleep(1)



    subscriber = node.create_subscription(UInt8MultiArray,"torque_feedback",status_callback,10)

    try:
       rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()