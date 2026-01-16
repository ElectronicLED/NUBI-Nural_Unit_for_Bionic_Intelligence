#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from vision_msgs.msg import Detection2DArray
from sensor_msgs.msg import Image,CameraInfo
from depthai_ros_msgs.msg import SpatialDetectionArray
import numpy as np
import time
from cv_bridge import CvBridge
import math,json

with open("coco_dataset.json", "r") as f:
    COCO_dict = json.load(f)  # load JSON from the file

class camera_handler(Node):
    def __init__(self):
        super().__init__('camera_handler')

        # --- Parameters ---
        self.input_topic = '/color/yolov4_Spatial_detections'
        # Subscriber and publisher
        self.sub = self.create_subscription(
            SpatialDetectionArray,
            self.input_topic,
            self.detections_callback,
            10
        )
        self.get_logger().info("DepthAI object reader started")

    def detections_callback(self, msg: SpatialDetectionArray):
        for det in msg.detections:
            if len(det.results)== 0:
                continue
            class_id = int(det.results[0].class_id)
            score = det.results[0].score
            class_name = COCO_dict.get(class_id+1, "unknown")

            # x right +ve / left -ve
            """
                object
                *
                  /|
                 / |   ← z (forward)
                /  |
        camera *---+
                    x (left/right)
            """
            x_m = det.position.x
            z_m = det.position.z
            y_m = det.position.y
            true_distance = math.sqrt(x_m**2 + y_m**2 + z_m**2)
            angle_rad = math.atan2(x_m, z_m)
            angle_deg = math.degrees(angle_rad)

            self.get_logger().info(
                f"{class_name} | z: {z_m:.2f} m | x: {x_m:.2f} m | {angle_deg:.1f}° | confidence {score}",
                throttle_duration_sec = 1.0
            )

def main(args=None):
    rclpy.init(args=args)
    node = camera_handler()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
