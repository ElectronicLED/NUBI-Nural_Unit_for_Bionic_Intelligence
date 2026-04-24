#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from moveit_msgs.srv import GetPositionIK
from geometry_msgs.msg import PoseStamped


class IKClient(Node):

    def __init__(self):
        super().__init__('ik_client')

        self.cli = self.create_client(GetPositionIK, '/compute_ik')

        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for /compute_ik service...')

        self.get_logger().info('IK service ready ✅')

        self.run_loop()

    def run_loop(self):
        while rclpy.ok():
            user_input = input("\nEnter x y z (or q to quit): ")

            if user_input.lower() == 'q':
                break

            try:
                x, y, z = map(float, user_input.split())
                self.call_ik(x, y, z)
            except:
                self.get_logger().error("Format: x y z")

        rclpy.shutdown()

    def call_ik(self, x, y, z):

        request = GetPositionIK.Request()

        request.ik_request.group_name = "left_arm"
        request.ik_request.ik_link_name = "left_arm_tcp"
        request.ik_request.timeout.sec = 2

        pose = PoseStamped()
        pose.header.frame_id = "base_lin"
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z
        pose.pose.orientation.w = 1.0

        request.ik_request.pose_stamped = pose

        self.get_logger().info(f"Computing IK for x={x}, y={y}, z={z}")

        future = self.cli.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        response = future.result()

        if response.error_code.val == 1:
            self.get_logger().info("IK Solution Found ✅")

            joint_names = response.solution.joint_state.name
            joint_positions = response.solution.joint_state.position

            print("\nJoint Angles (radians):")
            for name, pos in zip(joint_names, joint_positions):
                print(f"{name}: {pos:.4f}")

        else:
            self.get_logger().error("IK Failed ❌")


def main():
    rclpy.init()
    node = IKClient()
    rclpy.spin(node)


if __name__ == '__main__':
    main()