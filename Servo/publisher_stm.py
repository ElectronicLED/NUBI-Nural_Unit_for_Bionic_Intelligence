
#!usr/bin/env python3 

import rclpy
from std_msgs.msg import Int16MultiArray


def main():
    rclpy.init()
    node = rclpy.create_node("LAPTOP_PUB_NODE")
    publisher = node.create_publisher(Int16MultiArray,"LED_color_cmd",10)

    msg = Int16MultiArray()
    id_val = int(input("Enter the ID: "))
    color_val = input("Enter the Color: ")
    match color_val:
        case "green":
            int_color = 1
        case "blue":
            int_color = 2
        case "cyan":
            int_color = 3
        case "red":
            int_color = 4
        case "yellow":
            int_color = 5
        case "pink":
            int_color = 6
        case "white":
            int_color = 7
        
    msg.data = [id_val, int_color]
    publisher.publish(msg)

    #def timer_callback():
    #    msg = Int16MultiArray()
    #    msg.data = [0,0]
    #    for i in range(len(msg.data)):
    #        msg.data[i] = int(input(f"Enter the angle of index {i}: "))
    #    publisher.publish(msg)
    #    node.get_logger().info(f"\n---------------------")
    #    for i in range (len(msg.data)):
    #        node.get_logger().info(f"The servo angle {i} is {int(msg.data[i])} deg")
    node.destroy_node()
    rclpy.shutdown()



    #timer = node.create_timer(1.5,timer_callback)

    #try:
    #   rclpy.spin(node)
    #except KeyboardInterrupt:
    #    pass
    #finally:
    #    node.destroy_node()
    #    rclpy.shutdown()

if __name__ == "__main__":
    main()