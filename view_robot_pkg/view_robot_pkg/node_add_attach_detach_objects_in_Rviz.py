#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose
from moveit_msgs.msg import CollisionObject, AttachedCollisionObject
from shape_msgs.msg import SolidPrimitive
import os

class DualArmSceneManager(Node):
    def __init__(self):
        super().__init__('dual_arm_scene_manager')
        
        # Publishers for MoveIt Planning Scene
        self.scene_pub = self.create_publisher(CollisionObject, 'collision_object', 10)
        self.attached_pub = self.create_publisher(AttachedCollisionObject, 'attached_collision_object', 10)
        
        # IMPORTANT: Replace these with the actual last link names of your arms
        self.arm_links = {
            "left": "link_left_palm",  
            "right": "link_right_palm"
        }
        
        self.get_logger().info(">>> Dual Arm Scene Manager initialized.")

    def add_box(self, name, x, y, z, sx, sy, sz):
        obj = CollisionObject()
        obj.header.frame_id = "world" 
        obj.id = name
        
        primitive = SolidPrimitive()
        primitive.type = SolidPrimitive.BOX
        primitive.dimensions = [sx, sy, sz]
        
        pose = Pose()
        pose.position.x = x
        pose.position.y = y
        pose.position.z = z
        pose.orientation.w = 1.0
        
        obj.primitives.append(primitive)
        obj.primitive_poses.append(pose)
        obj.operation = CollisionObject.ADD
        
        self.scene_pub.publish(obj)
        self.get_logger().info(f"Adding box: {name}")

    def attach_box(self, name, side):
        if side not in self.arm_links:
            self.get_logger().error("Invalid side! Choose 'left' or 'right'.")
            return

        attached_obj = AttachedCollisionObject()
        attached_obj.link_name = self.arm_links[side]
        attached_obj.object.id = name
        attached_obj.object.header.frame_id = self.arm_links[side]
        attached_obj.object.operation = CollisionObject.ADD
        
        self.attached_pub.publish(attached_obj)
        self.get_logger().info(f"Attaching {name} to {side} arm ({self.arm_links[side]})")

    def remove_box(self, name):
        obj = CollisionObject()
        obj.id = name
        obj.operation = CollisionObject.REMOVE
        self.scene_pub.publish(obj)
        self.get_logger().info(f"Removing box: {name}")

def main(args=None):
    rclpy.init(args=args)
    manager = DualArmSceneManager()

    try:
        while rclpy.ok():
            print("\nCommands: [add, attach_l, attach_r, remove, exit]")
            task = input("Enter command: ").strip().lower()
            
            if task == "add":
                manager.add_box("package1", 0.0, 0.5, 0.2, 0.05, 0.05, 0.05)
            elif task == "attach_l":
                manager.attach_box("package1", "left")
            elif task == "attach_r":
                manager.attach_box("package1", "right")
            elif task == "remove":
                manager.remove_box("package1")
            elif task == "exit":
                break
            
            rclpy.spin_once(manager, timeout_sec=0.1)
            
    except KeyboardInterrupt:
        pass
    finally:
        manager.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()