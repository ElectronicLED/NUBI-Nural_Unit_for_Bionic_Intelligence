#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient

from moveit_msgs.action import MoveGroup
from moveit_msgs.msg import MotionPlanRequest, Constraints, PositionConstraint
from shape_msgs.msg import SolidPrimitive
from geometry_msgs.msg import PoseStamped

import math
import time
import matplotlib.pyplot as plt


# 🔥 FINAL REAL WORKSPACE FILTER (based on your measurements)
def is_valid_region(x, y, z):

    # hard limits
    if x < 0.03 or x > 0.20:
        return False

    # 🔥 updated Y range (includes overlap region)
    if y < -0.08 or y > 0.25:
        return False

    if z < -0.12 or z > 0.20:
        return False

    # curved workspace constraint
    r = math.sqrt(x**2 + y**2)
    if r > 0.26:
        return False

    # shrink at extreme heights
    if z > 0.15 and r > 0.18:
        return False

    if z < -0.05 and r > 0.15:
        return False

    return True


class WorkspaceScanner(Node):

    def __init__(self):
        super().__init__("left_arm_workspace_scanner")

        self._action_client = ActionClient(self, MoveGroup, 'move_action')

        self.get_logger().info("Waiting for MoveIt...")
        self._action_client.wait_for_server()
        self.get_logger().info("MoveIt ready ✔")

    def check_point(self, x, y, z):

        goal_msg = MoveGroup.Goal()
        request = MotionPlanRequest()

        request.group_name = "left_arm"
        request.allowed_planning_time = 1.0
        request.num_planning_attempts = 1

        pose = PoseStamped()
        pose.header.frame_id = "base_lin"
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z
        pose.pose.orientation.w = 1.0

        pc = PositionConstraint()
        pc.header = pose.header
        pc.link_name = "left_arm_tcp"

        primitive = SolidPrimitive()
        primitive.type = SolidPrimitive.SPHERE
        primitive.dimensions = [0.01]

        pc.constraint_region.primitives.append(primitive)
        pc.constraint_region.primitive_poses.append(pose.pose)
        pc.weight = 1.0

        constraints = Constraints()
        constraints.position_constraints.append(pc)

        request.goal_constraints.append(constraints)

        goal_msg.request = request
        goal_msg.planning_options.plan_only = True  # 🔥 no movement

        future = self._action_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, future)

        goal_handle = future.result()

        if not goal_handle.accepted:
            return False

        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future)

        result = result_future.result().result

        return result.error_code.val == 1


def plot_workspace(reachable, unreachable):

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    if reachable:
        x, y, z = zip(*reachable)
        ax.scatter(x, y, z, label='Reachable', s=10)

    if unreachable:
        x, y, z = zip(*unreachable)
        ax.scatter(x, y, z, label='Unreachable', s=5)

    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')

    ax.set_title("Left Arm Workspace (Final)")
    ax.legend()

    plt.show()


def main():

    rclpy.init()
    node = WorkspaceScanner()

    # 🔥 Focused region (based on your real limits)
    x_vals = [0.03 + i * 0.02 for i in range(9)]     # 0.03 → 0.20
    y_vals = [-0.08 + i * 0.02 for i in range(17)]   # -0.08 → 0.25
    z_vals = [-0.12 + i * 0.02 for i in range(17)]   # -0.12 → 0.20

    reachable = []
    unreachable = []

    total = 0

    # count valid points
    for x in x_vals:
        for y in y_vals:
            for z in z_vals:
                if is_valid_region(x, y, z):
                    total += 1

    print(f"Total valid points: {total}")

    count = 0

    for x in x_vals:
        for y in y_vals:
            for z in z_vals:

                if not is_valid_region(x, y, z):
                    continue

                count += 1
                print(f"[{count}/{total}] ({x:.2f}, {y:.2f}, {z:.2f})")

                success = node.check_point(x, y, z)

                if success:
                    reachable.append((x, y, z))
                else:
                    unreachable.append((x, y, z))

                time.sleep(0.01)

    print("\n=== SUMMARY ===")
    print(f"Reachable: {len(reachable)}")
    print(f"Unreachable: {len(unreachable)}")

    node.destroy_node()
    rclpy.shutdown()

    plot_workspace(reachable, unreachable)


if __name__ == "__main__":
    main()
