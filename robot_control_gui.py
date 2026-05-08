import os
from servoControlGUI_fancy import *
from robot import *
from jsongui import *

class robot_control_buttons(QWidget):
    def __init__(self):
        super().__init__()
        self.robot_controller = robot_actions_controller()
        self.initlayout()
    
    def initlayout(self):
        # Removed hard-coded stance buttons; actions now available in `jsonGUI` via "Do All"
        self.vlayout = QVBoxLayout()
        self.setLayout(self.vlayout)

class robotGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.jsonGUI = jsonGUI() 
        self.robot_control_buttons = robot_control_buttons()
        self.servo_control_gui = servoGUI()
        self.initlayout()

    def initlayout(self):
        # Wire jsonGUI to read action time from the servo control GUI spinbox
        self.jsonGUI.action_time_source = lambda: self.servo_control_gui.action_time
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


def ros_spin(node):
    # Use a per-node executor if this helper is used; matches other modules.
    executor = rclpy.executors.SingleThreadedExecutor()
    try:
        executor.add_node(node)
        executor.spin()
    finally:
        try:
            executor.remove_node(node)
        except Exception:
            pass

if __name__ == "__main__":
    rclpy.init()
    os.environ["QT_SCALE_FACTOR"] = "0.9"
    app = QApplication(sys.argv)
    robot_control_gui= robotGUI()
    robot_control_gui.showNormal()

    app.exec()
    # Clean up nodes (each GUI class spins its own node thread)
    try:
        robot_control_gui.servo_control_gui.ros_node.destroy_node()
    except Exception:
        pass
    try:
        robot_control_gui.jsonGUI.node.destroy_node()
    except Exception:
        pass
    try:
        rclpy.shutdown()
    except Exception:
        pass
    sys.exit(0)