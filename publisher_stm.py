
#!usr/bin/env python3 

import rclpy
from std_msgs.msg import Int16MultiArray


def main():
    rclpy.init()
    node = rclpy.create_node("LAPTOP_PUB_NODE")
    publisher = node.create_publisher(Int16MultiArray,"legs_command",10)

    def timer_callback():
        msg = Int16MultiArray()
        msg.data = [0,0,0,0,0,0,0,0,5,5,5,5]
        publisher.publish(msg)
        node.get_logger().info(f"\n---------------------")
        for i in range (len(msg.data)):
            node.get_logger().info(f"The servo angle {i} is {int(msg.data[i])} deg")



    timer = node.create_timer(1.5,timer_callback)

    try:
       rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()