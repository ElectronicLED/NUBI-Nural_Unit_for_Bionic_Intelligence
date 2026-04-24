#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import MotionPlanRequest, Constraints, PositionConstraint
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import PoseStamped

import subprocess
import time


class MoveToXYZ(Node):

    def __init__(self):
        super().__init__("move_to_xyz_test")

        self.ensure_moveit_running()

        self._action_client = ActionClient(self, MoveGroup, 'move_action')
        self.get_logger().info("Waiting for MoveIt action server...")
        self._action_client.wait_for_server()

        self.get_logger().info("MoveIt ready ✔")


    def ensure_moveit_running(self):

        try:
            result = subprocess.run(
                ["ros2", "action", "list"],
                capture_output=True,
                text=True
            )

            if "/move_action" not in result.stdout:
                self.get_logger().info("MoveIt not running → launching move_group")

                subprocess.Popen([
                    "ros2",
                    "launch",
                    "moveit_robot_arm_sim2",
                    "move_group.launch.py"
                ])

                time.sleep(5)

        except Exception as e:
            self.get_logger().error(f"Failed to start MoveIt: {e}")


    def execute_motion(self, x, y, z, group, tcp):

        goal_msg = MoveGroup.Goal()
        request = MotionPlanRequest()

        request.group_name = group
        request.allowed_planning_time = 5.0
        request.num_planning_attempts = 10

        request.max_velocity_scaling_factor = 0.9
        request.max_acceleration_scaling_factor = 0.9

        pose = PoseStamped()

        # 🔥 CHANGE 1: use camera frame
        pose.header.frame_id = "camera_link"

        # 🔥 CHANGE 2: add timestamp (IMPORTANT for TF)
        pose.header.stamp = self.get_clock().now().to_msg()

        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z

        # keep simple orientation
        pose.pose.orientation.w = 1.0

        position_constraint = PositionConstraint()
        position_constraint.header = pose.header
        position_constraint.link_name = tcp

        primitive = SolidPrimitive()
        primitive.type = SolidPrimitive.SPHERE
        primitive.dimensions = [0.03]

        position_constraint.constraint_region.primitives.append(primitive)
        position_constraint.constraint_region.primitive_poses.append(pose.pose)
        position_constraint.weight = 1.0

        constraints = Constraints()
        constraints.position_constraints.append(position_constraint)

        request.goal_constraints.append(constraints)

        goal_msg.request = request
        goal_msg.planning_options.plan_only = False

        self.get_logger().info(
            f"Planning + Executing {group} → ({x}, {y}, {z}) in CAMERA frame"
        )

        future = self._action_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, future)

        goal_handle = future.result()

        if not goal_handle.accepted:
            self.get_logger().error("Goal rejected")
            return

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        result = result_future.result().result

        if result.error_code.val == 1:
            self.get_logger().info("Motion executed successfully")

            rclpy.spin_once(self, timeout_sec=0.1)
            time.sleep(0.5)

        else:
            self.get_logger().error(f"Execution failed code {result.error_code.val}")


def main():

    rclpy.init()
    node = MoveToXYZ()

    while rclpy.ok():

        arm = input("\nSelect arm (L = left, R = right, q = quit): ").lower()

        if arm == 'q':
            break

        if arm == 'l':
            group = "left_arm"
            tcp = "left_arm_tcp"
        elif arm == 'r':
            group = "right_arm"
            tcp = "right_arm_tcp"
        else:
            print("Invalid option")
            continue

        user_input = input("Enter x y z (camera frame): ")

        try:
            x, y, z = map(float, user_input.split())
            node.execute_motion(x, y, z, group, tcp)
        except:
            print("Format: x y z")

    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()