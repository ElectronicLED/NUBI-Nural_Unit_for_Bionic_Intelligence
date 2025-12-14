
#!usr/bin/env python3 

import rclpy
from std_msgs.msg import Int16MultiArray


def main():
    rclpy.init()
    node = rclpy.create_node("LAPTOP_SUB_NODE")
    
    def sub_callback(msg):
        node.get_logger().info(f"\n---------------------")
        for i in range(len(msg.data)):
            node.get_logger().info(f"{i}The angle is {msg.data[i]}")
    
    
    Subscriber = node.create_subscription(Int16MultiArray,"legs_feedback",sub_callback,10)

    try:
       rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()