from subClasses.servo_subclasses import *
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import QRect,Qt,QObject,pyqtSignal
from PyQt6.QtGui import QKeySequence, QPixmap,QPalette,QBrush
import sys
import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32,Int16MultiArray,Bool

#the id of the servos in this list should be at its respective
#index in the low level handling
#put the required hotkey as well
legs_command_servos_order =   [ 16, 6,  7,  8, 10,  9, 17,  11,12, 13, 15, 14]
legs_command_servos_hotkeys = ['q','w','e','r','t','y','u','i','o','p','[',']']
upperbody_command_servos_order =   [ 0,  1,  2,  3,  4,  5,  19]
upperbody_command_servos_hotkeys = ['a','s','d','f','g','h','j']
torque_hotkey = "z"

def ros_spin(node):
    rclpy.spin(node)

class servoGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.ros_node = ServoControlROSNode()
        self.initlayout()
        self.place_servoSubwidgets()
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

        for servo_id,servo_key in (
                        list(zip(legs_command_servos_order, legs_command_servos_hotkeys)) +
                        list(zip(upperbody_command_servos_order, upperbody_command_servos_hotkeys))
                    ):
            self.servo_control_subWidgets_dict[servo_id] = servo_control_subWidget(
                hotkey = str(servo_key),
                id = servo_id)
            self.servo_control_subWidgets_dict[servo_id].update_angle_signal.connect(
                self.update_servo_position)
            self.servo_control_subWidgets_dict[servo_id].move(positions[servo_id][0],
                                                              positions[servo_id][1])        
        xTorque,Ytorque = 50,50
        self.torque_lock_widget = torque_control_subWidget(torque_hotkey)
        self.torque_lock_widget.move(xTorque,Ytorque)
        self.ros_node.legs_callback_signal.connect(self.update_legs_servo_subwidgets)
        self.ros_node.upperbody_callback_signal.connect(self.update_upperbody_servo_subwidgets)
        #used for shifting incrementing/decrementing
        self.increment = True

    def update_legs_servo_subwidgets(self,angles_list:Int16MultiArray):
        for i, id in enumerate(legs_command_servos_order):
            self.servo_control_subWidgets_dict[id].set_angle(angles_list[i])

    def update_upperbody_servo_subwidgets(self,angles_list:Int16MultiArray):
        for i, id in enumerate(upperbody_command_servos_order):
            self.servo_control_subWidgets_dict[id].set_angle(angles_list[i])

    def get_all_legs_angles(self):
        try:
            return [int(self.servo_control_subWidgets_dict[id].get_angle()) for id in legs_command_servos_order]
        except ValueError as e:
            print(f"Error getting legs angles: {e}, check that the angles are being read and are not None")
            return False

    def get_all_upperbody_angles(self):
        try:
            return [int(self.servo_control_subWidgets_dict[id].get_angle()) for id in upperbody_command_servos_order]
        except ValueError as e:
            print(f"Error getting upperbody angles: {e}, check that the angles are being read and are not None")
            return False

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
            self.torque_lock_widget.toggle_torque()
            self.ros_node.publish_torque(self.torque_lock_widget.torque_lock_status)
            print(f"Torque Lock: {self.torque_lock_widget.torque_lock_status}")
            
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
        if servo_widget.id in legs_command_servos_order:
            all_angles = self.get_all_legs_angles()
            if not all_angles:
                return
            new_servo_angle = int(servo_widget.get_angle())+sign*1
            all_angles[legs_command_servos_order.index(servo_widget.id)] = new_servo_angle
            self.ros_node.publish_legs_angles(all_angles)
            print(f"Updated legs angles: {all_angles}")
        elif servo_widget.id in upperbody_command_servos_order:
            all_angles = self.get_all_upperbody_angles()
            if not all_angles:
                return
            new_servo_angle = int(servo_widget.get_angle())+sign*1
            all_angles[upperbody_command_servos_order.index(servo_widget.id)] = new_servo_angle
            self.ros_node.publish_upperbody_angles(all_angles)
            print(f"Updated upperbody angles: {all_angles}")

if __name__ == "__main__":
    rclpy.init()
    app = QApplication(sys.argv)
    servogui_window = servoGUI()
    servogui_window.show()

    app.exec()
    servogui_window.ros_node.destroy_node()
    rclpy.shutdown()
    sys.exit(0)