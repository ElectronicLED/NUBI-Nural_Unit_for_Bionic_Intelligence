#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import tf2_ros
import math
import time
from rclpy.duration import Duration


# quaternion → euler
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

        self.base_frame = "base_lin"

        # 🔥 BOTH grippers
        self.ee_frames = [
            "left_arm_tcp",
            "right_arm_tcp"
        ]

        self.get_logger().info("Waiting for TF...")
        time.sleep(2)  # allow TF to start

        # print every 0.5 sec
        self.timer = self.create_timer(0.5, self.print_state)

    def print_single(self, ee_frame):

        try:
            transform = self.tf_buffer.lookup_transform(
                self.base_frame,
                ee_frame,
                rclpy.time.Time(),
                timeout=Duration(seconds=0.5)
            )

            p = transform.transform.translation
            q = transform.transform.rotation

            roll, pitch, yaw = euler_from_quaternion([q.x, q.y, q.z, q.w])

            print(f"\n[{ee_frame}]")
            print(f"Position → x={p.x:.3f}, y={p.y:.3f}, z={p.z:.3f}")
            print(f"Euler    → roll={roll:.2f}, pitch={pitch:.2f}, yaw={yaw:.2f}")

        except Exception:
            print(f"\n[{ee_frame}] ❌ TF not available yet")

    def print_state(self):

        print("\n===== GRIPPERS STATE =====")

        for ee in self.ee_frames:
            self.print_single(ee)

        print("\n---------------------------")


def main():
    rclpy.init()
    node = EEStateMonitor()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
