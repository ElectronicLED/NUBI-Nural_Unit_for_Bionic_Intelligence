from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtGui import QKeySequence, QPixmap,QPalette,QBrush
from PyQt6.QtCore import Qt,pyqtSignal,QObject
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32,Int16MultiArray,Bool,UInt8MultiArray
from rclpy.publisher import Publisher

servo_legs_sub_topic = "/legs_feedback"
servo_legs_pub_topic = "/legs_command"
Legs = "Legs"
servo_upperbody_sub_topic = "/upperbody_feedback"
servo_upperbody_pub_topic = "/upperbody_command"
Upperbody = "Upperbody"
torque_pub_topic = "/torque_command"
torque_feedback_sub_topic = "/torque_feedback"

class ServoControlROSNode(Node, QObject):
    angles_callback_signal = pyqtSignal(str, list)
    torque_feedback_signal = pyqtSignal(int)
    def __init__(self):
        # must run rclpy.init() before it, here we run it in name == main
        Node.__init__(self, 'servo_gui_ros_node')
        QObject.__init__(self)

        # dynamic publisher cache: topic_name -> publisher
        self._dynamic_publishers: dict[str, Publisher] = {}

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
        self.torque_feedback_sub = self.create_subscription(
            UInt8MultiArray,
            torque_feedback_sub_topic,
            self.torque_feedback_callback,
            10
        )
        self.torque_pub = self.create_publisher(
            Bool,torque_pub_topic,10
        )

    def publish_generic(self, topic_name: str, data_type: type, msg) -> None:
        """Publish `msg` to `topic_name` using `data_type`, creating a cached publisher as needed."""
        if topic_name not in self._dynamic_publishers:
            try:
                pub = self.create_publisher(data_type, topic_name, 10)
            except Exception as e:
                print(f"Failed to create publisher for {topic_name}: {e}")
                return
            self._dynamic_publishers[topic_name] = pub
        pub = self._dynamic_publishers[topic_name]
        try:
            pub.publish(msg)
        except Exception as e:
            print(f"Failed to publish to {topic_name}: {e}")

    def legs_callback(self, msg: Int16MultiArray):
        self.angles_callback_signal.emit(Legs,msg.data)
    
    def upperbody_callback(self, msg: Int16MultiArray):
        self.angles_callback_signal.emit(Upperbody,msg.data)
    
    def torque_feedback_callback(self, msg: UInt8MultiArray):
        self.torque_feedback_signal.emit(msg.data[0])

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
servo_widget_width = 57
class servo_control_subWidget(QWidget):
    parent = None
    width = None
    update_angle_signal = pyqtSignal(object,int)  # servo_id, angle
    def __init__(self,hotkey,id,command_name: str = None):
        super().__init__(servo_control_subWidget.parent)
        self.id = id
        self.angle = 0
        self.hotkey = hotkey
        # name of the command_array/group this servo belongs to
        self.command_name = command_name
        # Backward/ergonomic alias: some code refers to `servo_widget.name`
        self.name = command_name
        self.initLayoutVer()

    def initLayoutVer(self):
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(servo_control_subWidget.width) 
        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(2,0,0,0)
        self.vlayout.setSpacing(3)

        self.angle_label = QLabel("θ: None")
        
        self.hotkey_label = QLabel(f"Id:{self.id} | {self.hotkey} ")
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
            background: rgba(235, 174, 52, 180);
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

    def set_angle(self,num:int):
        if type(num) != int:
            print(f"Error: angle must be int, got {type(num)}")
            return
        self.angle = num
        self.angle_label.setText(f"θ: {num}")

    def increment(self):
        self.update_angle_signal.emit(self,1)
        print("Signal to increment servo id:",self.id)
    def decrement(self):
        self.update_angle_signal.emit(self,-1)
        print("Signal to decrement servo id:",self.id)
    def initLayoutHor(self):
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(servo_control_subWidget.width) 

        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(3,3,3,3)
        self.vlayout.setSpacing(1)

        self.name_label = QLabel(f"Id: {str(self.id)}")
        self.angle_label = QLabel("θ: None")
        
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
            background: rgba(235, 174, 52, 150);
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
    
class torque_control_subWidget(QWidget):
    parent = None
    toggle_requested = pyqtSignal()
    def __init__(self,toggle_key,name=None):
        super().__init__(torque_control_subWidget.parent) 
        self.torque_lock_status = None
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

            QWidget[state="gray"] {
                background: rgb(128, 128, 128);
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
        self.turn_gray()
        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(3,10,3,10)
        self.vlayout.setSpacing(0)
        self.torque_lock_label = QLabel("Torque Lock")

        self.torque_lock_status_label = QLabel('None')

        self.torque_lock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)        
        self.torque_lock_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)        
        self.toggle_btn = QPushButton(f"Toggle with {toggle_key}",self)
        # Connect logic (Signals & Slots)
        self.toggle_btn.clicked.connect(self.toggle_requested.emit)
        self.vlayout.addWidget(self.torque_lock_label)
        self.vlayout.addWidget(self.torque_lock_status_label)
        self.vlayout.addWidget(self.toggle_btn)

    def turn_green(self):
        self.setProperty("state", "green")
        self.style().unpolish(self)
        self.style().polish(self)

    def turn_red(self):
        self.setProperty("state", "red")
        self.style().unpolish(self)
        self.style().polish(self)

    def turn_gray(self):
        self.setProperty("state", "gray")
        self.style().unpolish(self)
        self.style().polish(self)

    def set_torque_state(self, state):
        """Set torque state: None (gray), True (green), or False (red)"""
        self.torque_lock_status = state
        if state is None:
            self.torque_lock_status_label.setText('None')
            self.turn_gray()
        elif state:
            self.torque_lock_status_label.setText('On')
            self.turn_green()
        else:
            self.torque_lock_status_label.setText('Off')
            self.turn_red()

    def set_torque_timeout(self):
        """Display timeout message when no feedback received for 5+ seconds."""
        self.torque_lock_status = None
        self.torque_lock_status_label.setText('No reading\nreceived for\npast 5 seconds')
        self.turn_gray()

#can be much better but good enough for now
def return_servo_subWidgets_positions(bg:QPixmap)->dict[int,tuple[int,int]]:
    centerx = int(bg.size().width()/2)-15
    servo_control_subWidget.width = servo_widget_width
    #shift is the pixel distance from center to the start of servo widgets on the right side
    shift3 =  79
    shift4 = 164
    shift5 = 127
    shift11 = 330
    shift12 = 60
    shift17 = 45
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
    x18 = x5
    x19 = shift19
    x20 = x5+20
    x21 = -x20-servo_widget_width
                                                            #servo 18 not implemented in low level
    x_shifts = [x0,x1,x2,x3,x4,x5,x6,x7,x8,x9,x10,x11,x12,x13,x14,x15,x16,x17,x18,x19,x20,x21]

    y0  = 140
    y1  = 136
    y2  = 260
    y3  = y0
    y4  = y1
    y5  = y2
    y6  = 310
    y7  = 345
    y8  = 435
    y9  = 525
    y10 = 510
    y11 = y6
    y12 = y7
    y13 = y8
    y14 = y9
    y15 = y10
    y16 = y17 = 255
    y18 = y5
    y19 = 175
    y20 = y12
    y21 = y7
    y_values = [y0,y1,y2,y3,y4,y5,y6,y7,y8,y9,y10,y11,y12,y13,y14,y15,y16,y17,y18,y19,y20,y21]
    
    # combine into dict
    positions = {i: (centerx + x_shifts[i], y_values[i]) for i in range(len(x_shifts))}
    return positions
