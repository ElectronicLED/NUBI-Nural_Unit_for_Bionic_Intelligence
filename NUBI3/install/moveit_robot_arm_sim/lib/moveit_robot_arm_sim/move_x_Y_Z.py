#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import (
    MotionPlanRequest,
    Constraints,
    PositionConstraint,
    OrientationConstraint
)

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

                self.get_logger().info(
                    "MoveIt not running → launching move_group"
                )

                subprocess.Popen([
                    "ros2",
                    "launch",
                    "moveit_robot_arm_sim",
                    "demo.launch.py"
                ])

                time.sleep(6)

        except Exception as e:
            self.get_logger().error(f"Failed to start MoveIt: {e}")


    def execute_motion(self, x, y, z, group, tcp):

        goal_msg = MoveGroup.Goal()

        request = MotionPlanRequest()

        request.group_name = group

        request.allowed_planning_time = 10.0
        request.num_planning_attempts = 10

        request.max_velocity_scaling_factor = 0.3
        request.max_acceleration_scaling_factor = 0.3

        request.start_state.is_diff = True

        pose = PoseStamped()

        # Use camera frame
        pose.header.frame_id = "camera_link"

        # Timestamp important for TF
        pose.header.stamp = self.get_clock().now().to_msg()

        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z

        # Simple forward orientation
        pose.pose.orientation.x = 0.0
        pose.pose.orientation.y = 0.0
        pose.pose.orientation.z = 0.0
        pose.pose.orientation.w = 1.0

        constraints = Constraints()

        # =========================
        # POSITION CONSTRAINT
        # =========================

        position_constraint = PositionConstraint()

        position_constraint.header = pose.header
        position_constraint.link_name = tcp

        primitive = SolidPrimitive()

        primitive.type = SolidPrimitive.SPHERE

        # tolerance sphere radius
        primitive.dimensions = [0.02]

        position_constraint.constraint_region.primitives.append(
            primitive
        )

        position_constraint.constraint_region.primitive_poses.append(
            pose.pose
        )

        position_constraint.weight = 1.0

        constraints.position_constraints.append(
            position_constraint
        )

        # =========================
        # ORIENTATION CONSTRAINT
        # =========================

        orientation_constraint = OrientationConstraint()

        orientation_constraint.header = pose.header
        orientation_constraint.link_name = tcp

        orientation_constraint.orientation = pose.pose.orientation

        orientation_constraint.absolute_x_axis_tolerance = 0.3
        orientation_constraint.absolute_y_axis_tolerance = 0.3
        orientation_constraint.absolute_z_axis_tolerance = 0.3

        orientation_constraint.weight = 1.0

        constraints.orientation_constraints.append(
            orientation_constraint
        )

        request.goal_constraints.append(constraints)

        goal_msg.request = request

        goal_msg.planning_options.plan_only = False

        self.get_logger().info(
            f"\nPlanning + Executing"
            f"\nGroup : {group}"
            f"\nTCP   : {tcp}"
            f"\nTarget: ({x}, {y}, {z})"
            f"\nFrame : camera_link"
        )

        future = self._action_client.send_goal_async(goal_msg)

        rclpy.spin_until_future_complete(self, future)

        goal_handle = future.result()

        if not goal_handle.accepted:

            self.get_logger().error("Goal rejected")
            return

        self.get_logger().info("Goal accepted ✔")

        result_future = goal_handle.get_result_async()

        rclpy.spin_until_future_complete(self, result_future)

        result = result_future.result().result

        if result.error_code.val == 1:

            self.get_logger().info(
                "Motion executed successfully ✔"
            )

        else:

            self.get_logger().error(
                f"Execution failed code: "
                f"{result.error_code.val}"
            )


def main():

    rclpy.init()

    node = MoveToXYZ()

    while rclpy.ok():

        arm = input(
            "\nSelect arm "
            "(L = left, R = right, q = quit): "
        ).lower()

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

        user_input = input(
            "Enter target x y z "
            "(camera frame): "
        )

        try:

            x, y, z = map(float, user_input.split())

            node.execute_motion(
                x,
                y,
                z,
                group,
                tcp
            )

        except Exception as e:

            print(f"Invalid format: {e}")
            print("Example: 0.3 0.1 0.4")

    node.destroy_node()

    rclpy.shutdown()


if __name__ == '__main__':
    main()
