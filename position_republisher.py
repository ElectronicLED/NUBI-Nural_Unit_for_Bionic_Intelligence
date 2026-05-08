#!/usr/bin/env python3
"""
position_republisher.py

Simulates robot motion for testing purposes when the physical robot is absent.
Subscribes to command topics and republishes them as feedback topics,
assuming commanded positions are immediately reached.

Topics:
  Subscribed:  /upperbody_command  (std_msgs/Int16MultiArray)
               /legs_command       (std_msgs/Int16MultiArray)
               /status_command     (std_msgs/Int16MultiArray)
  Published:   /upperbody_feedback (std_msgs/Int16MultiArray)
               /legs_feedback      (std_msgs/Int16MultiArray)

Protocol (status_command):
  CMD_MOVE_ONE = 8  →  data = [8, servo_id, angle, play_time]
    Updates the single servo's slot in the relevant feedback array and republishes.
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Int16MultiArray
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

_BE_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=1
)

# Must match STM_microROS.ino motor index arrays exactly
_LEG_SERVO_IDS   = [16, 6, 7, 8, 10, 9, 17, 18, 12, 13, 15, 14]  # 12 entries
_UPPER_SERVO_IDS = [0, 1, 2, 3, 4, 11, 19]                         # 7 entries

CMD_MOVE_ONE = 8


class PositionRepublisher(Node):
    def __init__(self):
        super().__init__('position_republisher')

        self.upperbody_feedback_pub = self.create_publisher(
            Int16MultiArray, 'upperbody_feedback', _BE_QOS
        )
        self.legs_feedback_pub = self.create_publisher(
            Int16MultiArray, 'legs_feedback', _BE_QOS
        )

        # Internal state arrays — updated by all command sources
        self._legs_state  = [0] * len(_LEG_SERVO_IDS)
        self._upper_state = [0] * len(_UPPER_SERVO_IDS)

        self.create_subscription(
            Int16MultiArray,
            'upperbody_command',
            self._upperbody_cmd_callback,
            _BE_QOS,
        )
        self.create_subscription(
            Int16MultiArray,
            'legs_command',
            self._legs_cmd_callback,
            _BE_QOS,
        )
        self.create_subscription(
            Int16MultiArray,
            'status_command',
            self._status_cmd_callback,
            _BE_QOS,
        )

        self.get_logger().info(
            'PositionRepublisher started — forwarding commands to feedback topics.'
        )

        # Publish zero positions immediately on startup
        self._publish_legs()
        self._publish_upper()

        self.get_logger().info('Published zero positions on startup.')

    # ── helpers ────────────────────────────────────────────────────────────────
    def _publish_legs(self):
        msg = Int16MultiArray()
        msg.data = list(self._legs_state)
        self.legs_feedback_pub.publish(msg)
        self.get_logger().debug(f'legs_feedback: {self._legs_state}')

    def _publish_upper(self):
        msg = Int16MultiArray()
        msg.data = list(self._upper_state)
        self.upperbody_feedback_pub.publish(msg)
        self.get_logger().debug(f'upperbody_feedback: {self._upper_state}')

    # ── callbacks ──────────────────────────────────────────────────────────────
    def _upperbody_cmd_callback(self, msg: Int16MultiArray):
        data = list(msg.data)
        self._upper_state[:len(data)] = data[:len(self._upper_state)]
        self._publish_upper()

    def _legs_cmd_callback(self, msg: Int16MultiArray):
        data = list(msg.data)
        self._legs_state[:len(data)] = data[:len(self._legs_state)]
        self._publish_legs()

    def _status_cmd_callback(self, msg: Int16MultiArray):
        if not msg.data:
            return
        cmd = msg.data[0]
        if cmd == CMD_MOVE_ONE and len(msg.data) >= 3:
            servo_id = int(msg.data[1])
            angle    = int(msg.data[2])
            if servo_id in _LEG_SERVO_IDS:
                idx = _LEG_SERVO_IDS.index(servo_id)
                self._legs_state[idx] = angle
                self._publish_legs()
                self.get_logger().debug(
                    f'CMD_MOVE_ONE: legs servo {servo_id} (idx {idx}) → {angle}°'
                )
            elif servo_id in _UPPER_SERVO_IDS:
                idx = _UPPER_SERVO_IDS.index(servo_id)
                self._upper_state[idx] = angle
                self._publish_upper()
                self.get_logger().debug(
                    f'CMD_MOVE_ONE: upper servo {servo_id} (idx {idx}) → {angle}°'
                )


def main(args=None):
    rclpy.init(args=args)
    node = PositionRepublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
