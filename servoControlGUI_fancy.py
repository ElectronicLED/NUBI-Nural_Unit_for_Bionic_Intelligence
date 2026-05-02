from subClasses.servo_subclasses import *
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QSpinBox
from PyQt6.QtCore import QRect,Qt,QObject,pyqtSignal,QTimer
from PyQt6.QtGui import QKeySequence, QPixmap,QPalette,QBrush
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
        #self.setGeometry(QRect(100,100,200,300))
        # ===== Load background image =====
        self.bg = QPixmap("robot.jpg")

        # Resize window to image size
        self.setFixedSize(self.bg.size())

        # Set background
        palette = self.palette()
        palette.setBrush(
            QPalette.ColorRole.Window,
            QBrush(self.bg)
        )
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def place_servoSubwidgets(self):        
        servo_control_subWidget.parent=self
        torque_control_subWidget.parent = self
        positions = return_servo_subWidgets_positions(self.bg)
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
                self.servo_control_subWidgets_dict[servo_id].move(positions[servo_id][0],
                                                                  positions[servo_id][1])        
        xTorque,Ytorque = 50,25
        self.torque_lock_widget = torque_control_subWidget(torque_hotkey)
        self.torque_lock_widget.move(xTorque,Ytorque)
        self.torque_lock_widget.toggle_requested.connect(self.toggle_torque)
        self.ros_node.angles_callback_signal.connect(self.handle_angles_callback)
        self.ros_node.torque_feedback_signal.connect(self.handle_torque_feedback)
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
     
        #used for shifting incrementing/decrementing
        self.increment = True

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
        msg.data = all_angles
        self.ros_node.publish_generic(pub_topic, pub_type, msg)
        print(f"Published {command.name} angles: {all_angles}")

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