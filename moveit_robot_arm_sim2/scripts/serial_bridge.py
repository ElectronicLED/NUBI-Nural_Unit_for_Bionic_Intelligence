import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_msgs.msg import Int16MultiArray
import math


class JointToAngleConverter(Node):

    def __init__(self):
        super().__init__('joint_to_angle_converter')

        # Order required by STM32
        # -R1, -R2, -R3, -L1, -L2, -L3, Torso
        self.joint_mapping = [
            'Rshoulder_pitch',
            'Rshoulder_roll',
            'Relbow_roll',
            'Lshoulder_pitch',
            'Lshoulder_roll',
            'Lelbow_roll',
            'Upper_body_joint'
        ]

        self.filename = "trajectory.txt"

        with open(self.filename, "w") as f:
            f.write("// Order: -R1,-R2,-R3,-L1,-L2,-L3,Torso\n")
            f.write("const int motion_path[][7] = {\n")

        self.publisher_ = self.create_publisher(
            Int16MultiArray,
            "upperbody_command",
            10
        )

        self.subscription = self.create_subscription(
            JointState,
            "joint_states",
            self.listener_callback,
            10
        )

        # Store last valid joint command
        self.last_command = None

        # Publish timer (smooth motion)
        self.timer = self.create_timer(0.05, self.publish_command)  # 20 Hz

        self.get_logger().info("Optimal bridge started (20 Hz synchronized publishing)")


    def listener_callback(self, msg):

        current_joints = dict(zip(msg.name, msg.position))

        try:
            command = []

            for i, joint_name in enumerate(self.joint_mapping):

                if joint_name not in current_joints:
                    return

                rad = current_joints[joint_name]
                deg = int(rad * 180.0 / math.pi)

                # Invert arms only
                if i < 6:
                    deg = -deg

                command.append(deg)

            self.last_command = command

        except Exception as e:
            self.get_logger().error(f"Conversion error: {e}")


    def publish_command(self):

        if self.last_command is None:
            return

        msg = Int16MultiArray()
        msg.data = self.last_command

        self.publisher_.publish(msg)

        # Save trajectory
        data_str = ", ".join(map(str, self.last_command))

        with open(self.filename, "a") as f:
            f.write(f"  {{{data_str}}},\n")

        self.get_logger().info(f"Sent: {self.last_command}")


    def destroy_node(self):

        with open(self.filename, "a") as f:
            f.write("};\n")

        super().destroy_node()


def main(args=None):

    rclpy.init(args=args)

    node = JointToAngleConverter()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
