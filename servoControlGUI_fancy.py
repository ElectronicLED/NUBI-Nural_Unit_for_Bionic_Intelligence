from subClasses.servo_subclasses import *
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import QRect,Qt,QObject,pyqtSignal
from PyQt6.QtGui import QKeySequence, QPixmap,QPalette,QBrush
import sys
import threading
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
              hotkey_array = ['q','w','e','r','t','y','u','i','o','p','[',']'])

command_array(name = Upperbody,
              ids_array = [0, 1, 2, 3, 4, 5, 19],
              hotkey_array = ['a','s','d','f','g','h','j'])

command_array(name = "Grippers",
              ids_array = [20, 21],
              hotkey_array = ['b', 'n'])

all_commands_dict = command_array.all_commands_dict
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

        for command_array in (all_commands_dict.values()):
            for servo_id, servo_key in zip(command_array.ids_array, command_array.hotkey_array):
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
        self.ros_node.angles_callback_signal.connect(self.handle_angles_callback)
     
        #used for shifting incrementing/decrementing
        self.increment = True

    #ros node subscribe callbacks
    def handle_angles_callback(self, name:str, angles_list:list[int]):
        for i, id in enumerate(all_commands_dict[name].ids_array):
            self.servo_control_subWidgets_dict[id].set_angle(angles_list[i])

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
        for command_array in all_commands_dict.values():
            if servo_widget.id in command_array.ids_array:
                all_angles = self.get_all_servo_angles_in_same_command_array(command_array)
                if not all_angles:
                    return
                new_servo_angle = int(servo_widget.get_angle())+sign*1
                all_angles[command_array.ids_array.index(servo_widget.id)] = new_servo_angle
                self.ros_node.publish_legs_angles(all_angles)
                print(f"Published {command_array.name} angles: {all_angles}")
                return
        else: print(f"Servo widget id {servo_widget.id} not found in any command array, cannot update position")

if __name__ == "__main__":
    rclpy.init()
    app = QApplication(sys.argv)
    servogui_window = servoGUI()
    servogui_window.show()

    app.exec()
    servogui_window.ros_node.destroy_node()
    rclpy.shutdown()
    sys.exit(0)