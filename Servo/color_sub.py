#!usr/bin/env python3 

import rclpy
from std_msgs.msg import Int16MultiArray
import time


def main():
    rclpy.init()
    node = rclpy.create_node("LAPTOP_SUB_NODE")

    def color_detect(int_color):
        color_val = " "
        match int_color:
            case 0:
                color_val = "nothing"
            case 1:
                color_val = "green"
            case 2:
                color_val = "blue"
            case 3:
                color_val = "cyan"
            case 4:
                color_val = "red"
            case 5:
                color_val = "yellow"
            case 6:
                color_val = "pink"
            case 7:
                color_val = "white"
        return color_val

    def status_callback(msg):
        node.get_logger().info(f"---------------------------------------------------------")
        node.get_logger().info(f"The color of each servo is:")
        for i in range(20):
            if msg.data[i] == 255:
                node.get_logger().info(f"Checksum in packet")
            else:
                node.get_logger().info(f"Servo {i} color is {color_detect(msg.data[i])}")
        node.get_logger().info(f"---------------------------------------------------------")
        node.get_logger().info(f"Done")
        time.sleep(1)



    subscriber = node.create_subscription(Int16MultiArray,"LED_color_feedback",status_callback,10)

    try:
       rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()