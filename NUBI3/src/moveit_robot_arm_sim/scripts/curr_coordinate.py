#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from tf2_ros import Buffer, TransformListener

import math


class LeftEEPosition(Node):

    def __init__(self):

        super().__init__("left_ee_position")

        # TF Buffer
        self.tf_buffer = Buffer()

        self.tf_listener = TransformListener(
            self.tf_buffer,
            self
        )

        # Timer
        self.timer = self.create_timer(
            0.5,
            self.print_ee_position
        )

        self.get_logger().info(
            "Left EE Position Node Started ✔"
        )

    def print_ee_position(self):

        try:

            # Transform:
            # FROM base
            # TO left end effector
            transform = self.tf_buffer.lookup_transform(
                "base_lin",
                "left_arm_tcp",
                rclpy.time.Time()
            )

            x = transform.transform.translation.x
            y = transform.transform.translation.y
            z = transform.transform.translation.z

            qx = transform.transform.rotation.x
            qy = transform.transform.rotation.y
            qz = transform.transform.rotation.z
            qw = transform.transform.rotation.w

            self.get_logger().info(
                f"\nLeft EE Position:"
                f"\nX: {x:.3f}"
                f"\nY: {y:.3f}"
                f"\nZ: {z:.3f}"
                f"\n"
                f"\nQuaternion:"
                f"\nqx: {qx:.3f}"
                f"\nqy: {qy:.3f}"
                f"\nqz: {qz:.3f}"
                f"\nqw: {qw:.3f}"
            )

        except Exception as e:

            self.get_logger().warn(
                f"TF not ready: {e}"
            )


def main():

    rclpy.init()

    node = LeftEEPosition()

    try:

        rclpy.spin(node)

    except KeyboardInterrupt:

        pass

    finally:

        node.destroy_node()

        rclpy.shutdown()


if __name__ == "__main__":

    main()
