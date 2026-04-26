#!usr/bin/env python3 

import rclpy
from std_msgs.msg import Int16MultiArray
import time


def main():
    rclpy.init()
    node = rclpy.create_node("LAPTOP_PUB_NODE")

    def status_callback(msg):
        node.get_logger().info(f"---------------------------------------------------------")
        node.get_logger().info(f"The status value for each servo is:")
        for i in range(20):
            node.get_logger().info(f"Servo {i}")
            node.get_logger().info(f"Status error is {msg.data[i*2]}")
            node.get_logger().info(f"Status detail is {msg.data[i*2 +1]}")
        node.get_logger().info(f"---------------------------------------------------------")
        node.get_logger().info(f"Done")
        time.sleep(1)



    subscriber = node.create_subscription(Int16MultiArray,"motor_status",status_callback,10)

    try:
       rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()