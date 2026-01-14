from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import QRect,Qt,pyqtSignal,QObject
from PyQt6.QtGui import QKeySequence, QPixmap,QPalette,QBrush
import sys
import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32,Int16MultiArray,Bool

servo_sub_topic = "/legs_feedback"
servo_pub_topic = "/legs_command"
torque_pub_topic = "/torque_command"
class ServoControlROSNode(Node, QObject):
    int_received = pyqtSignal(list)

    def __init__(self):
        # must run rclpy.init() before it, here we run it in name == main
        Node.__init__(self, 'servo_gui_ros_node')
        QObject.__init__(self)

        self.sub = self.create_subscription(
            Int16MultiArray,
            servo_sub_topic,
            self.callback,
            10
        )
        self.pub = self.create_publisher(
            Int16MultiArray,
            servo_pub_topic,
            10
        )

        self.torque_pub = self.create_publisher(
            Bool,torque_pub_topic,10
        )

    def callback(self, msg):
        self.int_received.emit(msg.data)
    
    def publish_angle(self,num:list[int]):
        msg = Int16MultiArray()
        msg.data = num   
        self.pub.publish(msg)

    def publish_torque(self,torque_lock:bool):
        self.torque_pub.publish(Bool(data=torque_lock)) 

def ros_spin(node):
    rclpy.spin(node)

class servo_control_widget(QWidget):
    parent = None
    width = None
    def __init__(self,upkey,name=None):
        super().__init__(servo_control_widget.parent) 
        self.count = 0
        self.upkey = upkey
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
                           background: rgba(235, 174, 52, 255);
                           border-radius: 8px;
                            """)
        self.setFixedWidth(servo_control_widget.width) 
        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(3,3,3,3)
        self.vlayout.setSpacing(0)
        self.angle_label = QLabel("0")
        self.angle_label.setStyleSheet("""
                                 color: white;
                                 """)
        self.name_label = QLabel(f"{name}")
        self.name_label.setStyleSheet("""
                                        color: white;
                                        """)
        self.angle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)        
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)        
        self.up_btn = QPushButton(f"+ {self.upkey}")
        # Connect logic (Signals & Slots)
        self.up_btn.clicked.connect(self.increment)
        self.vlayout.addWidget(self.name_label)
        self.vlayout.addWidget(self.up_btn)
        self.vlayout.addWidget(self.angle_label)
    def switch_sign(self):
        self.up_btn.setText(f"{'+' if self.up_btn.text()[0] == '-' else '-'} {self.upkey}")
    def get_angle(self) -> str:
        return self.angle_label.text()

    def set_angle(self,num):
        self.angle_label.setText(str(num))

    def increment(self):
        self.count += 1
        self.angle_label.setText(str(self.count))

    def decrement(self):
        self.count -= 1
        self.angle_label.setText(str(self.count))

class torque_control_widget(QWidget):
    parent = None
    def __init__(self,toggle_key,name=None):
        super().__init__(torque_control_widget.parent) 
        self.torque_lock_status = True
        self.toggle_key = toggle_key
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
                           background: rgba(235, 174, 52, 255);
                           border-radius: 8px;
                            """)
        self.setStyleSheet("""
                           background: rgba(235, 174, 52, 255);
                           border-radius: 8px;
                            """)
        self.setFixedWidth(100)
        if self.torque_lock_status:
            self.turn_green()
        else:
            self.turn_red() 
        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(3,3,3,3)
        self.vlayout.setSpacing(0)
        self.torque_lock_label = QLabel("Torque Lock")
        self.torque_lock_label.setStyleSheet("""
                                 color: white;
                                 """)
        self.torque_lock_status_label = QLabel('On' if self.torque_lock_status else 'Off')
        self.torque_lock_status_label.setStyleSheet("""
                                        color: white;
                                        """)
        self.torque_lock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)        
        self.torque_lock_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)        
        self.toggle_btn = QPushButton(f"Toggle")
        # Connect logic (Signals & Slots)
        self.toggle_btn.clicked.connect(self.toggle_torque)
        self.vlayout.addWidget(self.torque_lock_label)
        self.vlayout.addWidget(self.torque_lock_status_label)
        self.vlayout.addWidget(self.toggle_btn)

    def toggle_torque(self):
        self.torque_lock_status = not self.torque_lock_status
        self.torque_lock_status_label.setText("On" if self.torque_lock_status else "Off")
        if self.torque_lock_status:
            self.turn_green()
        else:
            self.turn_red()
    def turn_red(self):
        self.setStyleSheet("""
                           background: rgba(255, 0, 0, 255);
                           border-radius: 8px;
                            """)
    def turn_green(self):
        self.setStyleSheet("""
                           background: rgba(0, 255, 0, 255);
                           border-radius: 8px;
                            """)
class servoGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.ros_node = ServoControlROSNode()
        #self.setGeometry(QRect(100,100,200,300))
        # ===== Load background image =====
        bg = QPixmap("robot.jpg")

        # Resize window to image size
        self.setFixedSize(bg.size())

        # Set background
        palette = self.palette()
        palette.setBrush(
            QPalette.ColorRole.Window,
            QBrush(bg)
        )
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        centerx = int(bg.size().width()/2)-15
        servo_widget_width = 35
        servo_control_widget.width = servo_widget_width

        xTorque,Ytorque = 50,50

        shift17 = 56
        x16,x17 = centerx-shift17-servo_widget_width, centerx+shift17
        y16 = y17 = 255
        shift12 = 69
        x7,x12 = centerx-shift12-servo_widget_width,centerx+shift12
        y7 = y12 = 360
        x14 = x13 = x12
        x8 = x9 = x7
        y13 = y8 = 450
        y14 = y9 = 540
        shift11 = 338
        x6 ,x11 = centerx-shift11-servo_widget_width,centerx+shift11
        y6 = y11 = 320
        x10 = x6
        x15 = x11
        y10 = y15 = 519
        
        servo_control_widget.parent=self
        torque_control_widget.parent = self
        self.servo16_widget = servo_control_widget("q","16")
        self.servo6_widget  = servo_control_widget("w","6 ")
        self.servo7_widget  = servo_control_widget("e","7 ")
        self.servo8_widget  = servo_control_widget("r","8")
        self.servo10_widget = servo_control_widget("t","10")
        self.servo9_widget  = servo_control_widget("y","9")
        self.servo17_widget = servo_control_widget("u","17")
        self.servo11_widget = servo_control_widget("i","11")
        self.servo12_widget = servo_control_widget("o","12")
        self.servo13_widget = servo_control_widget("p","13")
        self.servo15_widget = servo_control_widget("[","15")
        self.servo14_widget = servo_control_widget("]","14")
        self.torque_lock_widget = torque_control_widget("z")
        self.allservoslayouts:list[servo_control_widget] =[
                            self.servo16_widget,
                            self.servo6_widget ,
                            self.servo7_widget ,
                            self.servo8_widget ,
                            self.servo10_widget,
                            self.servo9_widget ,
                            self.servo17_widget,
                            self.servo11_widget,
                            self.servo12_widget,
                            self.servo13_widget,
                            self.servo15_widget,
                            self.servo14_widget]
        
        self.servo16_widget.move(x16,y16)
        self.servo6_widget.move(x6,y6)  
        self.servo7_widget.move(x7,y7)  
        self.servo8_widget.move(x8,y8)  
        self.servo10_widget.move(x10,y10) 
        self.servo9_widget.move(x9,y9)  
        self.servo17_widget.move(x17,y17) 
        self.servo11_widget.move(x11,y11) 
        self.servo12_widget.move(x12,y12) 
        self.servo13_widget.move(x13,y13)
        self.servo15_widget.move(x15,y15)
        self.servo14_widget.move(x14,y14)
        self.torque_lock_widget.move(xTorque,Ytorque)
        self.ros_node.int_received.connect(self.subscriber_callback)
        #used for shifting incrementing/decrementing
        self.increment = True
    def subscriber_callback(self,angles_list:Int16MultiArray):
        for i in range(len(self.allservoslayouts)):
            self.allservoslayouts[i].set_angle(angles_list[i])

    def get_all_angles(self):
        return [int(servolayout.get_angle()) for servolayout in self.allservoslayouts]

    def keyPressEvent(self,event):
        print("yes")
        #always returns higher case
        key_pressed = QKeySequence(event.key()).toString().lower()
        if key_pressed == "shift":
            self.increment = not self.increment
            for servo_widget in self.allservoslayouts:
                servo_widget.switch_sign()
            return
        if key_pressed == self.torque_lock_widget.toggle_key:
            self.torque_lock_widget.toggle_torque()
            self.ros_node.publish_torque(self.torque_lock_widget.torque_lock_status)
            print(f"Torque Lock: {self.torque_lock_widget.torque_lock_status}")
        for servo_widget in self.allservoslayouts:
            sign = 1
            if servo_widget in [self.servo17_widget,self.servo12_widget, self.servo13_widget, self.servo14_widget,
                                self.servo15_widget]:
                sign = -1 
            if key_pressed == servo_widget.upkey:
                if self.increment:
                    if sign == 1:
                        servo_widget.increment()
                    else: servo_widget.decrement()
                    all_angles = self.get_all_angles()
                    print(all_angles)
                    self.ros_node.publish_angle(all_angles)
                else:
                    if sign == 1:
                        servo_widget.decrement()
                    else: servo_widget.increment()
                    all_angles = self.get_all_angles()
                    print(all_angles)
                    self.ros_node.publish_angle(all_angles)


if __name__ == "__main__":
    rclpy.init()
    app = QApplication(sys.argv)
    servogui_window = servoGUI()
    servogui_window.show()
    ros_thread = threading.Thread(
        target=ros_spin,
        args=(servogui_window.ros_node,),
        daemon=True
    )
    ros_thread.start()
    app.exec()
    servogui_window.ros_node.destroy_node()
    rclpy.shutdown()
    sys.exit(0)