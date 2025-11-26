#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
import numpy as np
import time

class ImuLowPass(Node):
    def __init__(self):
        super().__init__('imu_low_pass_node')

        # --- Parameters ---
        self.input_topic = 'imu'
        self.output_topic = 'imu_low_pass'
        self.output_hz = 5.0  # Hz, you can change this
        self.low_pass_cutoff = 5.0  # Hz, adjust based on IMU frequency

        # Compute alpha for low-pass filter
        self.dt = 1.0 / self.output_hz
        tau = 1.0 / (2 * np.pi * self.low_pass_cutoff)
        self.alpha = self.dt / (tau + self.dt)

        # State for low-pass filter
        self.acc_filtered = np.zeros(3)

        # Last time we published
        self.last_pub_time = time.time()

        # Subscriber and publisher
        self.sub = self.create_subscription(
            Imu,
            self.input_topic,
            self.imu_callback,
            10
        )
        self.pub = self.create_publisher(Imu, self.output_topic, 10)

    def imu_callback(self, msg: Imu):
        # Raw acceleration
        acc = np.array([msg.linear_acceleration.x,
                        msg.linear_acceleration.y,
                        msg.linear_acceleration.z])

        # Low-pass filter
        self.acc_filtered = self.acc_filtered + self.alpha * (acc - self.acc_filtered)

        # Publish at controlled rate
        now = time.time()
        if now - self.last_pub_time >= 1.0 / self.output_hz:
            self.last_pub_time = now
            out_msg = Imu()
            out_msg.header.stamp = self.get_clock().now().to_msg()
            out_msg.header.frame_id = msg.header.frame_id

            # Fill filtered acceleration
            out_msg.linear_acceleration.x = float(self.acc_filtered[0])
            out_msg.linear_acceleration.y = float(self.acc_filtered[1])
            out_msg.linear_acceleration.z = float(self.acc_filtered[2])

            # Keep orientation and angular velocity unchanged
            out_msg.orientation = msg.orientation
            out_msg.angular_velocity = msg.angular_velocity

            self.pub.publish(out_msg)

            # Print filtered acceleration
            print(f"Filtered Acc: x={self.acc_filtered[0]:.3f}, y={self.acc_filtered[1]:.3f}, z={self.acc_filtered[2]:.3f}")


def main(args=None):
    rclpy.init(args=args)
    node = ImuLowPass()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
