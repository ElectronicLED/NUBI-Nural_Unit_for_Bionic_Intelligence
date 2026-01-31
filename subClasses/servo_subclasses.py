from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtGui import QKeySequence, QPixmap,QPalette,QBrush
from PyQt6.QtCore import Qt,pyqtSignal,QObject
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32,Int16MultiArray,Bool

servo_legs_sub_topic = "/legs_feedback"
servo_legs_pub_topic = "/legs_command"
servo_upperbody_sub_topic = "/upperbody_feedback"
servo_upperbody_pub_topic = "/upperbody_command"
torque_pub_topic = "/torque_command"

class ServoControlROSNode(Node, QObject):
    legs_callback_signal = pyqtSignal(list)
    upperbody_callback_signal = pyqtSignal(list)

    def __init__(self):
        # must run rclpy.init() before it, here we run it in name == main
        Node.__init__(self, 'servo_gui_ros_node')
        QObject.__init__(self)

        self.legs_sub = self.create_subscription(
            Int16MultiArray,
            servo_legs_sub_topic,
            self.legs_callback,
            10
        )
        self.legs_pub = self.create_publisher(
            Int16MultiArray,
            servo_legs_pub_topic,
            10
        )
        self.upperbody_sub = self.create_subscription(
            Int16MultiArray,
            servo_upperbody_sub_topic,
            self.upperbody_callback,
            10
        )
        self.upperbody_pub = self.create_publisher(
            Int16MultiArray,
            servo_upperbody_pub_topic,
            10
        )
        self.torque_pub = self.create_publisher(
            Bool,torque_pub_topic,10
        )

    def legs_callback(self, msg):
        self.legs_callback_signal.emit(msg.data)
    
    def upperbody_callback(self, msg):
        self.upperbody_callback_signal.emit(msg.data)

    def publish_legs_angles(self,num:list[int]):
        msg = Int16MultiArray()
        msg.data = num   
        self.legs_pub.publish(msg)

    def publish_upperbody_angles(self,num:list[int]):
        msg = Int16MultiArray()
        msg.data = num   
        self.upperbody_pub.publish(msg)

    def publish_torque(self,torque_lock:bool):
        self.torque_pub.publish(Bool(data=torque_lock)) 

font_size = 14
class servo_control_subWidget(QWidget):
    parent = None
    width = None
    update_angle_signal = pyqtSignal(object,int)  # servo_id, angle
    def __init__(self,hotkey,id):
        super().__init__(servo_control_subWidget.parent) 
        self.id = id
        self.angle = 0
        self.hotkey = hotkey
        self.initLayoutHor()
    def initLayoutHor(self):
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(servo_control_subWidget.width) 

        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(3,3,3,3)
        self.vlayout.setSpacing(1)

        self.name_label = QLabel(f"Id: {str(self.id)}")
        self.angle_label = QLabel("θ: 0")
        
        self.hlayout = QHBoxLayout()
        self.hotkey_label = QLabel(f"{self.hotkey}")
        self.up_btn = QPushButton("^")
        self.down_btn = QPushButton("v")
        self.hlayout.addWidget(self.up_btn)
        self.hlayout.addWidget(self.hotkey_label)
        self.hlayout.addWidget(self.down_btn)
        # Connect logic (Signals & Slots)
        self.up_btn.clicked.connect(self.increment)
        self.down_btn.clicked.connect(self.decrement)
        #self.vlayout.addWidget(self.up_btn)
        self.vlayout.addWidget(self.name_label)
        self.vlayout.addLayout(self.hlayout)
        self.vlayout.addWidget(self.angle_label)
        #self.vlayout.addWidget(self.down_btn)
        self.setStyleSheet(f"""
            QWidget {{
            background: rgba(235, 174, 52, 255);
            border: 2px solid black;   /* outer border only */
            border-radius: 8px;
            }}
            QLabel {{
                color: white;
                font-weight: bold;
                font-size: {font_size}px;
                qproperty-alignment: AlignCenter;
                background: transparent;   /* important! */
                border: 0px solid black;
            }}
            QPushButton {{
                color: white;
                font-weight: bold;
                font-size: {font_size}px;
                background: transparent;   /* important! */
                border: 2px solid black;
            }}
            """)
    def initLayoutVer(self):
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(servo_control_subWidget.width) 

        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(3,3,3,3)
        self.vlayout.setSpacing(1)

        self.angle_label = QLabel("θ: None")
        
        self.hotkey_label = QLabel(f"Id:{self.id} | {self.hotkey}")
        self.up_btn = QPushButton("^")
        self.down_btn = QPushButton("v")

        # Connect logic (Signals & Slots)
        self.up_btn.clicked.connect(self.increment)
        self.down_btn.clicked.connect(self.decrement)
        self.vlayout.addWidget(self.up_btn)
        self.vlayout.addWidget(self.hotkey_label)
        self.vlayout.addWidget(self.angle_label)
        self.vlayout.addWidget(self.down_btn)
        self.setStyleSheet(f"""
            QWidget {{
            background: rgba(235, 174, 52, 255);
            border: 2px solid black;   /* outer border only */
            border-radius: 8px;
            }}
            QLabel {{
                color: white;
                font-weight: bold;
                font-size: {font_size}px;
                qproperty-alignment: AlignCenter;
                background: transparent;   /* important! */
                border: 0px solid black;
            }}
            QPushButton {{
                color: white;
                font-weight: bold;
                font-size: {font_size}px;
                background: transparent;   /* important! */
                border: 2px solid black;
            }}
            """)
    def switch_sign(self):
        self.up_btn.setText(f"{'+' if self.up_btn.text()[0] == '-' else '-'} {self.hotkey}")

    def get_angle(self) -> str:
        return self.angle_label.text()[3:]

    def set_angle(self,num):
        self.angle = num
        self.angle_label.setText(f"θ: {num}")

    def increment(self):
        self.update_angle_signal.emit(self,1)

    def decrement(self):
        self.update_angle_signal.emit(self,-1)

class torque_control_subWidget(QWidget):
    parent = None
    def __init__(self,toggle_key,name=None):
        super().__init__(torque_control_subWidget.parent) 
        self.torque_lock_status = True
        self.toggle_key = toggle_key
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget {
                border-radius: 5px;
            }

            QWidget[state="green"] {
                background: rgb(0, 170, 0);
            }

            QWidget[state="red"] {
                background: rgb(255, 0, 0);
            }

            QLabel {
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
            QPushButton {
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
            """)
        self.setFixedWidth(170)
        if self.torque_lock_status:
            self.turn_green()
        else:
            self.turn_red() 
        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(3,10,3,10)
        self.vlayout.setSpacing(0)
        self.torque_lock_label = QLabel("Torque Lock")

        self.torque_lock_status_label = QLabel('On' if self.torque_lock_status else 'Off')

        self.torque_lock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)        
        self.torque_lock_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)        
        self.toggle_btn = QPushButton(f"Toggle with {toggle_key}",self)
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

    def turn_green(self):
        self.setProperty("state", "green")
        self.style().unpolish(self)
        self.style().polish(self)

    def turn_red(self):
        self.setProperty("state", "red")
        self.style().unpolish(self)
        self.style().polish(self)

def return_servo_subWidgets_positions(bg:QPixmap)->dict[int,tuple[int,int]]:
    centerx = int(bg.size().width()/2)-15
    servo_widget_width = 55
    servo_control_subWidget.width = servo_widget_width
    #shift is the pixel distance from center to the start of servo widgets on the right side
    shift3 =  79
    shift4 = 164
    shift5 = 127
    shift11 = 338
    shift12 = 69
    shift17 = 50
    shift19 = 18

    x0  = -shift3-servo_widget_width
    x1  = -shift4-servo_widget_width
    x2  = -shift5-servo_widget_width
    x3  = +shift3
    x4  = +shift4
    x5  = +shift5
    x6  = -shift11-servo_widget_width
    x7  = x8  = x9  = -shift12-servo_widget_width
    x10 = x6
    x11 = +shift11
    x12 = x13 = x14 = shift12
    x15 = x11
    x16 = -shift17-servo_widget_width
    x17 = shift17
    x19 = shift19
    x_shifts = [x0,x1,x2,x3,x4,x5,x6,x7,x8,x9,x10,x11,x12,x13,x14,x15,x16,x17,0,x19]

    y0  = 140
    y1  = 166
    y2  = 270
    y3  = y0
    y4  = y1
    y5  = y2
    y6  = 320
    y7  = 360
    y8  = 450
    y9  = 540
    y10 = 519
    y11 = y6
    y12 = y7
    y13 = y8
    y14 = y9
    y15 = y10
    y16 = y17 = 255
    y19 = 175
    y_values = [y0,y1,y2,y3,y4,y5,y6,y7,y8,y9,y10,y11,y12,y13,y14,y15,y16,y17,0,y19]
    
    # combine into dict
    positions = {i: (centerx + x_shifts[i], y_values[i]) for i in range(len(x_shifts))}
    return positions
