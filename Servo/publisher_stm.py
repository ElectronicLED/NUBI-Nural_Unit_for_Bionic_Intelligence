
#!usr/bin/env python3 

import rclpy
from std_msgs.msg import Int16MultiArray


def main():
    rclpy.init()
    node = rclpy.create_node("LAPTOP_PUB_NODE")
    publisher = node.create_publisher(Int16MultiArray,"gripper_command",10)

    def timer_callback():
        msg = Int16MultiArray()
        msg.data = [0,0]
        for i in range(len(msg.data)):
            msg.data[i] = int(input(f"Enter the angle of index {i}: "))
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