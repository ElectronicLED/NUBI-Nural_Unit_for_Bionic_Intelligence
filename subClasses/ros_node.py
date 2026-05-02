from PyQt6.QtCore import pyqtSignal, QObject
from rclpy.node import Node
from std_msgs.msg import Int16MultiArray, Bool, UInt8MultiArray
from rclpy.publisher import Publisher

servo_legs_sub_topic      = "/legs_feedback"
servo_legs_pub_topic      = "/legs_command"
Legs                      = "Legs"
servo_upperbody_sub_topic = "/upperbody_feedback"
servo_upperbody_pub_topic = "/upperbody_command"
Upperbody                 = "Upperbody"
torque_pub_topic          = "/torque_command"
torque_feedback_sub_topic = "/torque_feedback"
motor_status_sub_topic    = "/motor_status"


class ServoControlROSNode(Node, QObject):
    angles_callback_signal = pyqtSignal(str, list)
    torque_feedback_signal = pyqtSignal(int)
    motor_status_signal    = pyqtSignal(list)  # full flat Int16MultiArray data

    def __init__(self):
        Node.__init__(self, 'servo_gui_ros_node')
        QObject.__init__(self)

        self._dynamic_publishers: dict[str, Publisher] = {}

        self.legs_sub = self.create_subscription(
            Int16MultiArray, servo_legs_sub_topic, self.legs_callback, 10)
        self.legs_pub = self.create_publisher(
            Int16MultiArray, servo_legs_pub_topic, 10)

        self.upperbody_sub = self.create_subscription(
            Int16MultiArray, servo_upperbody_sub_topic, self.upperbody_callback, 10)
        self.upperbody_pub = self.create_publisher(
            Int16MultiArray, servo_upperbody_pub_topic, 10)

        self.torque_feedback_sub = self.create_subscription(
            UInt8MultiArray, torque_feedback_sub_topic, self.torque_feedback_callback, 10)
        self.torque_pub = self.create_publisher(Bool, torque_pub_topic, 10)

        self.motor_status_sub = self.create_subscription(
            Int16MultiArray, motor_status_sub_topic, self.motor_status_callback, 10)

    # ── Publishers ────────────────────────────────────────────────────────────
    def publish_generic(self, topic_name: str, data_type: type, msg) -> None:
        if topic_name not in self._dynamic_publishers:
            try:
                self._dynamic_publishers[topic_name] = self.create_publisher(data_type, topic_name, 10)
            except Exception as e:
                print(f"Failed to create publisher for {topic_name}: {e}")
                return
        try:
            self._dynamic_publishers[topic_name].publish(msg)
        except Exception as e:
            print(f"Failed to publish to {topic_name}: {e}")

    def publish_legs_angles(self, num: list[int]):
        msg = Int16MultiArray(); msg.data = num
        self.legs_pub.publish(msg)

    def publish_upperbody_angles(self, num: list[int]):
        msg = Int16MultiArray(); msg.data = num
        self.upperbody_pub.publish(msg)

    def publish_torque(self, torque_lock: bool):
        self.torque_pub.publish(Bool(data=torque_lock))

    # ── Subscribers ───────────────────────────────────────────────────────────
    def legs_callback(self, msg: Int16MultiArray):
        self.angles_callback_signal.emit(Legs, msg.data)

    def upperbody_callback(self, msg: Int16MultiArray):
        self.angles_callback_signal.emit(Upperbody, msg.data)

    def torque_feedback_callback(self, msg: UInt8MultiArray):
        self.torque_feedback_signal.emit(msg.data[0])

    def motor_status_callback(self, msg: Int16MultiArray):
        self.motor_status_signal.emit(list(msg.data))
