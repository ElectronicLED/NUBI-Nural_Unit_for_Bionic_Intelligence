#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

import tf2_ros


class TransformPoint(Node):

    def __init__(self):
        super().__init__("transform_point")

        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

    def quaternion_to_rotation_matrix(self, qx, qy, qz, qw):
        return [
            [1 - 2*qy*qy - 2*qz*qz, 2*qx*qy - 2*qz*qw,     2*qx*qz + 2*qy*qw],
            [2*qx*qy + 2*qz*qw,     1 - 2*qx*qx - 2*qz*qz, 2*qy*qz - 2*qx*qw],
            [2*qx*qz - 2*qy*qw,     2*qy*qz + 2*qx*qw,     1 - 2*qx*qx - 2*qy*qy]
        ]

    def base_to_camera(self, x, y, z):

        # wait for TF
        while not self.tf_buffer.can_transform(
            "camera_link",
            "base_lin",
            rclpy.time.Time()
        ):
            rclpy.spin_once(self, timeout_sec=0.1)

        transform = self.tf_buffer.lookup_transform(
            "camera_link",
            "base_lin",
            rclpy.time.Time()
        )

        # translation
        tx = transform.transform.translation.x
        ty = transform.transform.translation.y
        tz = transform.transform.translation.z

        # rotation
        q = transform.transform.rotation
        R = self.quaternion_to_rotation_matrix(q.x, q.y, q.z, q.w)

        # rotate
        rx = R[0][0]*x + R[0][1]*y + R[0][2]*z
        ry = R[1][0]*x + R[1][1]*y + R[1][2]*z
        rz = R[2][0]*x + R[2][1]*y + R[2][2]*z

        # translate
        cx = rx + tx
        cy = ry + ty
        cz = rz + tz

        return cx, cy, cz


def main():
    rclpy.init()
    node = TransformPoint()

    print("\n Enter points in base_lin (type 'q' to quit)\n")

    while True:
        try:
            user_input = input(">>> ")

            # exit condition
            if user_input.lower() == 'q':
                break

            x, y, z = map(float, user_input.split())

            result = node.base_to_camera(x, y, z)

            print(f" Camera frame: ({result[0]:.3f}, {result[1]:.3f}, {result[2]:.3f})\n")

        except ValueError:
            print(" Format: x y z (example: 0.1 0.05 0.2)\n")
        except KeyboardInterrupt:
            break

    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
