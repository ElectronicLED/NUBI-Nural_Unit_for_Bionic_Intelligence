#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import tf2_ros
import math


# quaternion → euler (no dependency issues)
def euler_from_quaternion(q):
    x, y, z, w = q

    t0 = +2.0 * (w * x + y * z)
    t1 = +1.0 - 2.0 * (x * x + y * y)
    roll = math.atan2(t0, t1)

    t2 = +2.0 * (w * y - z * x)
    t2 = max(min(t2, 1.0), -1.0)
    pitch = math.asin(t2)

    t3 = +2.0 * (w * z + x * y)
    t4 = +1.0 - 2.0 * (y * y + z * z)
    yaw = math.atan2(t3, t4)

    return roll, pitch, yaw


class EEStateMonitor(Node):

    def __init__(self):
        super().__init__("ee_state_monitor")

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # 🔥 CHANGE THESE if needed
        self.base_frame = "base_lin"
        self.ee_frame = "left_arm_tcp"

        # print every 0.5 sec
        self.timer = self.create_timer(0.5, self.print_state)

    def print_state(self):

        try:
            transform = self.tf_buffer.lookup_transform(
                self.base_frame,
                self.ee_frame,
                rclpy.time.Time()
            )

            # position
            p = transform.transform.translation
            x, y, z = p.x, p.y, p.z

            # orientation
            q = transform.transform.rotation
            roll, pitch, yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])

            self.get_logger().info(
                f"Position → x={x:.3f}, y={y:.3f}, z={z:.3f}"
            )
            self.get_logger().info(
                f"Euler → roll={roll:.2f}, pitch={pitch:.2f}, yaw={yaw:.2f}"
            )
            self.get_logger().info("---------------------------")

        except Exception as e:
            self.get_logger().warn("Waiting for TF...")


def main():
    rclpy.init()
    node = EEStateMonitor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
