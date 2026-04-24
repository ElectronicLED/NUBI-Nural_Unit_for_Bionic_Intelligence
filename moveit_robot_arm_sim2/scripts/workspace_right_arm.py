#!/usr/bin/env python3

import rclpy
from rclpy.node import Node

from moveit_msgs.srv import GetPositionIK
from moveit_msgs.msg import PositionIKRequest
from geometry_msgs.msg import PoseStamped

import csv
import matplotlib.pyplot as plt
import math


class RightArmWorkspace(Node):

    def __init__(self):
        super().__init__("right_arm_workspace")

        self.ik_client = self.create_client(GetPositionIK, '/compute_ik')

        while not self.ik_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info("Waiting for IK service...")

        self.get_logger().info("IK Service ready ✔")

    def check_point(self, x, y, z):

        req = GetPositionIK.Request()

        ik_req = PositionIKRequest()
        ik_req.group_name = "right_arm"   # 🔥 RIGHT ARM

        pose = PoseStamped()
        pose.header.frame_id = "base_lin"
        pose.header.stamp = self.get_clock().now().to_msg()

        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z
        pose.pose.orientation.w = 1.0

        ik_req.pose_stamped = pose
        req.ik_request = ik_req

        future = self.ik_client.call_async(req)
        rclpy.spin_until_future_complete(self, future)

        result = future.result()

        if result is None:
            return False

        return result.error_code.val == 1


def save_points(filename, points):

    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["x", "y", "z"])
        writer.writerows(points)

    print(f"Saved {len(points)} → {filename}")


def plot_workspace(points):

    if not points:
        return

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    x, y, z = zip(*points)
    ax.scatter(x, y, z, s=8)

    ax.set_xlabel("X (base)")
    ax.set_ylabel("Y (base)")
    ax.set_zlabel("Z (base)")

    plt.title("Right Arm Workspace")
    plt.show()


def main():

    rclpy.init()
    node = RightArmWorkspace()

    # 🔥 YOUR LIMITS (RIGHT ARM)
    x_min, x_max = -0.18, 0.20
    y_min, y_max = -0.26, 0.05
    z_min, z_max = -0.12, 0.21

    # 🔥 RESOLUTION
    step = 0.02

    x_vals = [x_min + i * step for i in range(int((x_max - x_min)/step) + 1)]
    y_vals = [y_min + i * step for i in range(int((y_max - y_min)/step) + 1)]
    z_vals = [z_min + i * step for i in range(int((z_max - z_min)/step) + 1)]

    reachable = []
    unreachable = []

    total = 0

    for x in x_vals:
        for y in y_vals:
            for z in z_vals:
                # 🔥 OPTIONAL FILTER (same as left arm)
                if (x**2 + y**2) > 0.30**2:
                    continue
                total += 1

    print(f"Total points: {total}")

    count = 0

    for x in x_vals:
        for y in y_vals:
            for z in z_vals:

                if (x**2 + y**2) > 0.30**2:
                    continue

                count += 1
                print(f"[{count}/{total}] ({x:.3f}, {y:.3f}, {z:.3f})")

                success = node.check_point(x, y, z)

                if success:
                    reachable.append((x, y, z))
                else:
                    unreachable.append((x, y, z))

    print("\n=== DONE ===")
    print(f"Reachable: {len(reachable)}")
    print(f"Unreachable: {len(unreachable)}")

    save_points("reachable_points_right.csv", reachable)
    save_points("unreachable_points_right.csv", unreachable)

    node.destroy_node()
    rclpy.shutdown()

    plot_workspace(reachable)


if __name__ == "__main__":
    main()
