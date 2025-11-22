
#!usr/bin/env python3 

import rclpy
from std_msgs.msg import Int16


angle = 50
def main():
    rclpy.init()
    node = rclpy.create_node("NUBI_STM_NODE")
    publisher = node.create_publisher(Int16,"NUBI_STM_TOPIC",10)

    def timer_callback():
        global angle
        msg = Int16()
        msg.data = angle
        publisher.publish(msg)
        node.get_logger().info(f"The servo angle is {msg.data} deg")



    timer = node.create_timer(1,timer_callback)

    try:
       rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()