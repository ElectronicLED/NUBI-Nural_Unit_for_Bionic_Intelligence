from servoControlGUI_fancy import *
from robot import *
from jsongui import *
class robot_control_buttons(QWidget):
    def __init__(self):
        super().__init__()
        self.robot_controller = robot_actions_controller()
        self.initlayout()
    
    def initlayout(self):
        self.vlayout = QVBoxLayout()
        self.default_stance_button = QPushButton("Default Stance")
        self.default_stance_button.pressed.connect(self.robot_controller.default_stance)
        self.fight_stance_button = QPushButton("Fight Stance")
        self.fight_stance_button.pressed.connect(self.robot_controller.fight_stance)
        self.jab_stance_button = QPushButton("Jab Stance")
        self.jab_stance_button.pressed.connect(self.robot_controller.jab)
        self.cross_stance_button = QPushButton("Cross Stance")
        self.cross_stance_button.pressed.connect(self.robot_controller.cross)
        self.wave_stance_button = QPushButton("Wave Stance")
        self.wave_stance_button.pressed.connect(self.robot_controller.wave)
        self.squat_stance_button = QPushButton("Squat Stance")
        self.squat_stance_button.pressed.connect(self.robot_controller.squat)

        self.vlayout.addWidget(self.default_stance_button)
        self.vlayout.addWidget(self.fight_stance_button)
        self.vlayout.addWidget(self.jab_stance_button)
        self.vlayout.addWidget(self.cross_stance_button)
        self.vlayout.addWidget(self.wave_stance_button)
        self.vlayout.addWidget(self.squat_stance_button)
        self.setLayout(self.vlayout)

class robotGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.jsonGUI = jsonGUI() 
        self.robot_control_buttons = robot_control_buttons()
        self.servo_control_gui = servoGUI()
        self.initlayout()

    def initlayout(self):
        self.hlayout = QHBoxLayout()
        self.hlayout.addWidget(self.servo_control_gui)
        self.hlayout.addWidget(self.robot_control_buttons)
        self.hlayout.addWidget(self.jsonGUI)
        self.setLayout(self.hlayout)
    def keyPressEvent(self, event):
        # Forward all key events to servoGUI
        QApplication.sendEvent(self.servo_control_gui, event)
        # Optionally, also call default behavior
        super().keyPressEvent(event)
if __name__ == "__main__":
    rclpy.init()
    app = QApplication(sys.argv)
    robot_control_gui= robotGUI()
    robot_control_gui.show()
    ros_thread = threading.Thread(
        target=ros_spin,
        args=(robot_control_gui.servo_control_gui.ros_node,),
        daemon=True
    )
    ros_thread2 = threading.Thread(
        target=ros_spin,
        args=(robot_control_gui.jsonGUI.node,),
        daemon=True
    )
    ros_thread.start()
    ros_thread2.start()
    app.exec()
    robot_control_gui.servo_control_gui.ros_node.destroy_node()
    rclpy.shutdown()
    sys.exit(0)