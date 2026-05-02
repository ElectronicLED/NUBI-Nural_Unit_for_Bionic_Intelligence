from subClasses.ros_node import (ServoControlROSNode,
                                  servo_legs_pub_topic, servo_upperbody_pub_topic,
                                  Legs, Upperbody)
from subClasses.servo_widget import servo_control_subWidget
from subClasses.torque_widget import torque_control_subWidget
from subClasses.position_manager import (servo_widget_width, load_servo_positions,
                                          save_servo_positions, X_GROUP_FOR_ID,
                                          Y_GROUP_FOR_ID, return_servo_subWidgets_positions)
from subClasses.status_table import StatusReferenceTable
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QSpinBox, QFrame
from PyQt6.QtCore import QRect, Qt, QObject, pyqtSignal, QTimer, QSize, QEvent
from PyQt6.QtGui import QKeySequence, QPixmap, QPalette, QBrush, QPainter, QColor
import sys
import threading
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32,Int16MultiArray,Bool
from subClasses.myDataclasses import *
#the id of the servos in this list should be at its respective
#index in the low level handling
#put the required hotkey as well
#add positions for the subwidgets in the return_servo_subWidgets_positions function in servo_subclasses.py
command_array(name = Legs,
              ids_array= [16, 6 , 7 , 8, 10 , 9, 17,  11, 12, 13, 15, 14],
              hotkey_array = ['q','w','e','r','t','y','u','i','o','p','[',']'],
              pub_topic=servo_legs_pub_topic,
              pub_type=Int16MultiArray)

command_array(name = Upperbody,
              ids_array = [0, 1, 2, 3, 4, 18, 19],
              hotkey_array = ['a','s','d','f','g','h','j'],
              pub_topic=servo_upperbody_pub_topic,
              pub_type=Int16MultiArray)

command_array(name = "Grippers",
              ids_array = [20, 21],
              hotkey_array = ['b', 'n'])

all_commands_dict = command_array.all_commands_dict
torque_hotkey = "z"

def ros_spin(node):
    # Spin this node with its own SingleThreadedExecutor to avoid
    # interfering with other spins in separate threads.
    executor = rclpy.executors.SingleThreadedExecutor()
    try:
        executor.add_node(node)
        executor.spin()
    finally:
        try:
            executor.remove_node(node)
        except Exception:
            pass

class servoGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.ros_node = ServoControlROSNode()
        # step increment for servo changes (0-90)
        self.step = 10
        # torque feedback timeout tracking
        self.last_torque_feedback_time = None
        self.initlayout()
        self.place_servoSubwidgets()
        # Install app-level event filter so +/- work from any widget
        QApplication.instance().installEventFilter(self)
        # Setup timeout checker timer
        self.torque_timeout_timer = QTimer(self)
        self.torque_timeout_timer.setInterval(1000)  # check every second
        self.torque_timeout_timer.timeout.connect(self.check_torque_timeout)
        self.torque_timeout_timer.start()
        self.ros_thread = threading.Thread(
        target=ros_spin,
        args=(self.ros_node,),
        daemon=True)
        self.ros_thread.start()

    def initlayout(self):
        # ===== Load background image =====
        self.bg = QPixmap("robot_higher_res_cropped.png")
        # Expand the window a bit vertically so bottom widgets are not clipped
        extra_height = -60
        img_size = self.bg.size()
        img_size.setHeight(img_size.height() + extra_height)
        # Add a white sidebar to the right for the reference tables
        sidebar_width = 160
        self._img_width = img_size.width() - 70
        self._img_height = img_size.height()
        total_width = img_size.width() + sidebar_width
        self.setFixedSize(total_width, img_size.height())
        self.setAutoFillBackground(True)

    def paintEvent(self, event):
        painter = QPainter(self)
        # Draw the robot photo on the left
        painter.drawPixmap(0, 0, self._img_width, self._img_height, self.bg)
        # Fill the sidebar with white
        painter.fillRect(self._img_width, 0,
                         self.width() - self._img_width, self.height(),
                         QColor("white"))
        painter.end()

    def mousePressEvent(self, event):
        # Steal focus from any spinbox/textbox so hotkeys work immediately
        self.setFocus()
        super().mousePressEvent(event)

    def eventFilter(self, obj, event):
        # +/- step adjustment from anywhere in the app
        if event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key in (Qt.Key.Key_Plus, Qt.Key.Key_Equal):
                new_step = min(90, self.step + 10)
                self.step_spinBox.setValue(new_step)
                return True
            if key == Qt.Key.Key_Minus:
                new_step = max(0, self.step - 10)
                self.step_spinBox.setValue(new_step)
                return True
        if obj is getattr(self, '_action_time_spinbox_ref', None):
            if event.type() == QEvent.Type.KeyPress:
                if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Escape):
                    self.setFocus()
                    return True
        return super().eventFilter(obj, event)

    def place_servoSubwidgets(self):        
        servo_control_subWidget.parent=self
        servo_control_subWidget.width = servo_widget_width
        torque_control_subWidget.parent = self
        # Store centerX and current position arrays for drag/link/save logic
        self._centerx = int(self.bg.size().width() / 2) - 15
        self._x_shifts, self._y_values = load_servo_positions()
        positions = {i: (self._centerx + self._x_shifts[i], self._y_values[i])
                     for i in self._x_shifts}
        self.servo_control_subWidgets_dict:dict[int,servo_control_subWidget] = dict()

        for command_array in (all_commands_dict.values()):
            for servo_id, servo_key in zip(command_array.ids_array, command_array.hotkey_array):
                # pass command array name to subwidget so it knows its group
                self.servo_control_subWidgets_dict[servo_id] = servo_control_subWidget(
                    hotkey = str(servo_key),
                    id = servo_id,
                    command_name = command_array.name)
                self.servo_control_subWidgets_dict[servo_id].update_angle_signal.connect(
                    self.update_servo_position)
                self.servo_control_subWidgets_dict[servo_id].position_changed_signal.connect(
                    self.handle_widget_dragged)
                self.servo_control_subWidgets_dict[servo_id].move(positions[servo_id][0],
                                                                  positions[servo_id][1])        
        xTorque,Ytorque = 50,25
        self.torque_lock_widget = torque_control_subWidget(torque_hotkey)
        self.torque_lock_widget.move(xTorque,Ytorque)
        self.torque_lock_widget.toggle_requested.connect(self.toggle_torque)
        self.ros_node.angles_callback_signal.connect(self.handle_angles_callback)
        self.ros_node.torque_feedback_signal.connect(self.handle_torque_feedback)
        self.ros_node.motor_status_signal.connect(self.handle_motor_status_callback)
        # ── Status reference table ──
        self.status_ref_table = StatusReferenceTable(parent=self)
        self.status_ref_table.move(self._img_width - 240, 10)
        self.status_ref_table.show()
        # Step control slider + spinbox
        self.step_label = QLabel(f"Step: {self.step}", parent=self)
        self.step_slider = QSlider(Qt.Orientation.Horizontal, parent=self)
        self.step_slider.setRange(0, 90)
        self.step_slider.setValue(self.step)
        self.step_spinBox = QSpinBox(parent=self)
        self.step_spinBox.setRange(0, 90)
        self.step_spinBox.setValue(self.step)
        # Position them on the GUI
        step_label_x = 320
        self.step_label.move(step_label_x, 10)
        self.step_slider.move(step_label_x, 30)
        self.step_slider.resize(150, 20)
        self.step_spinBox.move(step_label_x + 150, 26)
        # Warning label above the spinbox when user types >90
        self.step_warning = QLabel("Step Size, Max angle is 90", parent=self)
        self.step_warning.setStyleSheet("color: red; font-weight: bold;")
        self.step_warning.move(step_label_x, 6)
        # Connect signals
        self.step_slider.valueChanged.connect(self.step_spinBox.setValue)
        self.step_spinBox.valueChanged.connect(self.step_slider.setValue)
        def _on_step_changed(val):
            # enforce max 90
            if val > 90:
                val = 90
                self.step_spinBox.setValue(90)
            self.step = val
            self.step_label.setText(f"Step: {self.step}")
        self.step_spinBox.valueChanged.connect(_on_step_changed)
        # show/hide warning when user types a too-large value
        def _on_editing_finished():
            try:
                txt = self.step_spinBox.text()
                val = int(txt)
            except Exception:
                val = self.step
            if val > 90:
                # show warning and clamp
                self.step_spinBox.setValue(90)
                self.step = 90
                self.step_label.setText(f"Step: {self.step}")
            else:
                pass
        self.step_spinBox.editingFinished.connect(_on_editing_finished)

        # Action time control
        self.action_time = 500
        self.action_time_label = QLabel("Action Time", parent=self)
        self.action_time_label.setStyleSheet("color: black; background-color: white; font-weight: bold;")
        self.action_time_label.adjustSize()
        self.action_time_spinBox = QSpinBox(parent=self)
        self.action_time_spinBox.setRange(0, 2856)
        self.action_time_spinBox.setValue(self.action_time)
        self.action_time_label.move(step_label_x, 58)
        self.action_time_spinBox.move(step_label_x + 95, 54)
        self.action_time_spinBox.resize(80, 22)
        self.action_time_label.show()
        self.action_time_spinBox.show()
        def _on_action_time_changed(val):
            self.action_time = val
        self.action_time_spinBox.valueChanged.connect(_on_action_time_changed)

        # Return focus to main window on Enter or Esc while spinbox is focused
        def _action_time_event_filter(obj, event):
            if event.type() == QEvent.Type.KeyPress:
                if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Escape):
                    self.setFocus()
                    return True
            return False
        self._action_time_filter = _action_time_event_filter
        self.action_time_spinBox.installEventFilter(self)
        self._action_time_spinbox_ref = self.action_time_spinBox

        #used for shifting incrementing/decrementing
        self.increment = True

    def handle_motor_status_callback(self, data: list):
        """Unpack /motor_status flat array: servo id n -> error=data[2n], detail=data[2n+1]."""
        for servo_id, widget in self.servo_control_subWidgets_dict.items():
            err_idx = 2 * servo_id
            det_idx = 2 * servo_id + 1
            if det_idx < len(data):
                widget.set_status(data[err_idx], data[det_idx])

    #ros node subscribe callbacks
    def handle_angles_callback(self, name:str, angles_list:list[int]):
        for i, id in enumerate(all_commands_dict[name].ids_array):
            self.servo_control_subWidgets_dict[id].set_angle(angles_list[i])

    def check_torque_timeout(self):
        """Check if torque feedback has timed out (no messages for 5+ seconds)."""
        if self.last_torque_feedback_time is None:
            # No messages received yet, nothing to check
            return
        
        elapsed = time.time() - self.last_torque_feedback_time
        if elapsed > 5.0:
            self.torque_lock_widget.set_torque_timeout()

    def handle_torque_feedback(self, torque_state: int):
        """Handle torque feedback from ROS node and update GUI widget.
        
        Args:
            torque_state: Integer value (0 or 1) from ROS feedback
        """
        # Record timestamp of this feedback message
        self.last_torque_feedback_time = time.time()
        # Convert int to bool: 0 -> False, 1 -> True
        torque_bool = bool(torque_state)
        self.torque_lock_widget.set_torque_state(torque_bool)

    def get_all_legs_angles(self):
        try:
            return [int(self.servo_control_subWidgets_dict[id].get_angle()) for id in all_commands_dict[Legs].ids_array]
        except ValueError as e:
            print(f"Error getting legs angles: {e}, check that the angles are being read and are not None")
            return False

    def get_all_upperbody_angles(self):
        try:
            return [int(self.servo_control_subWidgets_dict[id].get_angle()) for id in all_commands_dict[Upperbody].ids_array]
        except ValueError as e:
            print(f"Error getting upperbody angles: {e}, check that the angles are being read and are not None")
            return False

    def get_all_servo_angles_in_same_command_array(self,command_array:command_array):
        try:
            return [int(self.servo_control_subWidgets_dict[id].get_angle()) for id in command_array.ids_array]
        except ValueError as e:
            print(f"Error getting {command_array.name} angles: {e}, check that the angles are being read and are not None")
            return False

    def toggle_torque(self):
        new_state = not self.torque_lock_widget.torque_lock_status
        self.ros_node.publish_torque(new_state)
        print(f"Torque Lock: {new_state}")

    def keyPressEvent(self,event):
        #always returns higher case
        key_pressed = QKeySequence(event.key()).toString().lower()
        print(f"Key pressed: {key_pressed}")
        if key_pressed == "shift":
            self.increment = not self.increment
            for servo_widget in self.servo_control_subWidgets_dict.values():
                servo_widget.switch_sign()
            return

        if key_pressed in ("+", "="):
            new_step = min(90, self.step + 10)
            self.step_spinBox.setValue(new_step)
            return

        if key_pressed == "-":
            new_step = max(0, self.step - 10)
            self.step_spinBox.setValue(new_step)
            return
        
        if key_pressed == self.torque_lock_widget.toggle_key:
            self.toggle_torque()
            
        for servo_widget in self.servo_control_subWidgets_dict.values():            
            #note its is known that the aligning the axis correctly
            #results in the servos in mirrored positions to rotate in opposite directions
            #this can be handled if desired
            if key_pressed == servo_widget.hotkey:
                if self.increment:
                    servo_widget.increment()
                else:
                    servo_widget.decrement()                    

    def handle_widget_dragged(self, widget_id: int, new_abs_x: int, new_abs_y: int):
        """Move linked widgets and persist positions after a drag.

        Servos sharing the same x_shift column move together horizontally;
        servos sharing the same y row move together vertically.
        """
        new_x_shift = new_abs_x - self._centerx
        delta_x = new_x_shift - self._x_shifts[widget_id]
        delta_y = new_abs_y  - self._y_values[widget_id]

        # Collect all IDs that need updating (union of x-group and y-group)
        x_group = X_GROUP_FOR_ID.get(widget_id, [widget_id])
        y_group = Y_GROUP_FOR_ID.get(widget_id, [widget_id])
        all_affected = set(x_group) | set(y_group)

        # Update dicts first so every move() call uses consistent values
        for sid in x_group:
            self._x_shifts[sid] += delta_x
        for sid in y_group:
            self._y_values[sid] += delta_y

        # Move every affected widget to its new position
        for sid in all_affected:
            w = self.servo_control_subWidgets_dict.get(sid)
            if w:
                w.move(self._centerx + self._x_shifts[sid], self._y_values[sid])

        save_servo_positions(self._x_shifts, self._y_values)

    #sign is 1 or -1
    def update_servo_position(self,servo_widget:servo_control_subWidget,sign:int):
        command_dict = all_commands_dict
        try:
            command = command_dict[servo_widget.name]
        except Exception:
            print(f"Servo widget {servo_widget.id} has no valid command name; cannot publish")
            return

        all_angles = self.get_all_servo_angles_in_same_command_array(command)
        if not all_angles:
            return

        try:
            servo_index = command.ids_array.index(servo_widget.id)
        except ValueError:
            print(f"Servo widget id {servo_widget.id} not found in command '{command.name}'")
            return

        new_servo_angle = int(servo_widget.get_angle()) + sign * getattr(self, 'step', 1)
        all_angles[servo_index] = new_servo_angle

        pub_topic = getattr(command, 'pub_topic', None)
        pub_type = getattr(command, 'pub_type', None)
        if not pub_topic or not pub_type:
            print(f"Command '{command.name}' has no publisher info (pub_topic/pub_type); cannot publish")
            return

        msg = pub_type()
        # std_msgs messages used here all expose a `.data` field
        # Append action_time as the last element for legs and upperbody commands
        if command.name in (Legs, Upperbody):
            msg.data = all_angles + [getattr(self, 'action_time', 500)]
        else:
            msg.data = all_angles
        self.ros_node.publish_generic(pub_topic, pub_type, msg)
        print(f"Published {command.name} angles: {msg.data}")

if __name__ == "__main__":
    rclpy.init()
    app = QApplication(sys.argv)
    servogui_window = servoGUI()
    servogui_window.show()
    app.exec()

    # Clean up
    try:
        servogui_window.ros_node.destroy_node()
    except Exception:
        pass
    try:
        rclpy.shutdown()
    except Exception:
        pass
    sys.exit(0)