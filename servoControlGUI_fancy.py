from subClasses.ros_node import (ServoControlROSNode,
                                  servo_legs_pub_topic, servo_upperbody_pub_topic,
                                  Legs, Upperbody)
from subClasses.servo_widget import servo_control_subWidget
from subClasses.torque_widget import torque_control_subWidget
from subClasses.position_manager import (servo_widget_width, load_servo_positions,
                                          save_servo_positions, X_GROUP_FOR_ID,
                                          Y_GROUP_FOR_ID, return_servo_subWidgets_positions)
from subClasses.status_table import StatusReferenceTable
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider, QSpinBox, QFrame, QCheckBox, QDoubleSpinBox
from PyQt6.QtCore import QRect, Qt, QObject, pyqtSignal, QTimer, QSize, QEvent, QSettings
from PyQt6.QtGui import QKeySequence, QPixmap, QPalette, QBrush, QPainter, QColor
import sys
import threading
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32,Int16MultiArray
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
              ids_array = [0, 1, 2, 3, 4, 18, 19, 101, 102, 103, 104],
              hotkey_array = ['a','s','d','f','g','h','j','k','l',';',"'"],
              pub_topic=servo_upperbody_pub_topic,
              pub_type=Int16MultiArray)

# Standard (non-Herkulex) servo IDs and their display pin names
STD_SERVO_IDS = {101, 102, 103, 104}
STD_SERVO_DISPLAY: dict[int, str] = {101: "PB13", 102: "PB14", 103: "PB15", 104: "PA8"}

all_commands_dict = command_array.all_commands_dict
torque_hotkey = "z"
SERVO_ANGLE_LIMIT = 150
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
        # torque verification polling state
        self._torque_verify_count = 0
        self._torque_response_count = 0      # responses received during this verification round
        self._torque_verify_timer = QTimer(self)
        self._torque_verify_timer.setInterval(1000)
        self._torque_verify_timer.timeout.connect(self._torque_verify_tick)
        # fired 1 s after the 5th poll; if we got <5 responses, reset to None
        self._torque_timeout_timer = QTimer(self)
        self._torque_timeout_timer.setSingleShot(True)
        self._torque_timeout_timer.setInterval(1000)
        self._torque_timeout_timer.timeout.connect(self._torque_verify_timeout)
        # auto-poll timers (status and torque frequency controls)
        self._status_poll_timer = QTimer(self)
        self._status_poll_timer.timeout.connect(self.ros_node.request_status)
        self._torque_poll_timer = QTimer(self)
        self._torque_poll_timer.timeout.connect(self.ros_node.request_torque_status)
        self.initlayout()
        self.place_servoSubwidgets()
        # Install app-level event filter so +/- work from any widget
        QApplication.instance().installEventFilter(self)
        self.ros_node.angles_callback_signal.connect(self.handle_angles_callback)
        self.ros_node.torque_feedback_signal.connect(self.handle_torque_feedback)
        self.ros_node.motor_status_signal.connect(self.handle_motor_status_callback)
        self.ros_thread = threading.Thread(
        target=ros_spin,
        args=(self.ros_node,),
        daemon=True)
        self.ros_thread.start()
        # Ask for torque once shortly after startup (give ROS time to connect)
        QTimer.singleShot(800, self.ros_node.request_torque_status)

    def initlayout(self):
        # ===== Load background image =====
        self.bg = QPixmap("robot_higher_res_cropped.png")
        # Expand the window a bit vertically so bottom widgets are not clipped
        extra_height = -60
        img_size = self.bg.size()
        img_size.setHeight(img_size.height() + extra_height)
        # Add a white sidebar to the right for the reference tables
        sidebar_width = 210
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
                    command_name = command_array.name,
                    display_name = STD_SERVO_DISPLAY.get(servo_id),
                    show_torque = servo_id not in STD_SERVO_IDS)
                self.servo_control_subWidgets_dict[servo_id].update_angle_signal.connect(
                    self.update_servo_position)
                self.servo_control_subWidgets_dict[servo_id].position_changed_signal.connect(
                    self.handle_widget_dragged)
                self.servo_control_subWidgets_dict[servo_id].move(positions[servo_id][0],
                                                                  positions[servo_id][1])
                # std servos start at 90 (mid-range)
                if servo_id in STD_SERVO_IDS:
                    self.servo_control_subWidgets_dict[servo_id].set_angle(90)        
        xTorque,Ytorque = 50,25
        self.torque_lock_widget = torque_control_subWidget(torque_hotkey)
        self.torque_lock_widget.move(xTorque,Ytorque)
        self.torque_lock_widget.toggle_requested.connect(self.toggle_torque)
        self.torque_lock_widget.set_on_requested.connect(self.set_torque_on)
        self.torque_lock_widget.set_off_requested.connect(self.set_torque_off)
        # Error clear button — directly below the torque widget
        self.error_clear_btn = QPushButton("Clear Errors", parent=self)
        self.error_clear_btn.setStyleSheet(
            "QPushButton { background: #c0392b; color: white; font-weight: bold; "
            "font-size: 13px; border-radius: 4px; padding: 4px; }\n"
            "QPushButton:pressed { background: #96281b; }")
        self.error_clear_btn.resize(self.torque_lock_widget.width(), 30)
        # position set later (below action time box in sidebar)
        self.error_clear_btn.clicked.connect(self.ros_node.reset_error)
        self.error_clear_btn.show()
        self.status_ref_table = StatusReferenceTable(parent=self)
        self.status_ref_table.move(self._img_width - 240, 10)
        self.status_ref_table.show()
        # ── Sidebar polling controls ──────────────────────────────────────────
        sx = self._img_width + 6   # sidebar left edge
        # start below the status reference table
        sy = self.status_ref_table.y() + self.status_ref_table.height() + 10
        # Write white-checkmark SVG once so qt stylesheet can reference it
        import os as _os
        _check_svg = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "white_check.svg")
        if not _os.path.exists(_check_svg):
            with open(_check_svg, "w") as _f:
                _f.write('<svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 12 12">'
                         '<polyline points="1,7 4,11 11,1" stroke="white" fill="none" stroke-width="2.2"/>'
                         '</svg>')
        _check_svg_escaped = _check_svg.replace("\\", "/")
        _cb_ss = ("QCheckBox {{ color: black; background: transparent; spacing: 5px; }}\n"
                  "QCheckBox::indicator {{ width: 15px; height: 15px; background: black; "
                  "border: 1px solid #888; border-radius: 2px; }}\n"
                  "QCheckBox::indicator:checked {{ background: black; border: 1px solid #aaa; "
                  "image: url({check}); }}\n").format(check=_check_svg_escaped)
        _ss = "color: black; background: transparent;"
        _btn_ss = ("QPushButton { background: #2980b9; color: white; font-weight: bold; "
                   "font-size: 12px; border-radius: 4px; padding: 3px; }\n"
                   "QPushButton:pressed { background: #1a5276; }")
        sidebar_w = self.width() - self._img_width - 8

        # --- Status section ---
        self.status_auto_cb = QCheckBox("Auto", parent=self)
        self.status_auto_cb.setStyleSheet(_cb_ss)
        self.status_auto_cb.move(sx, sy)
        self.status_auto_cb.adjustSize()
        self.status_freq_label = QLabel("Status Frequency", parent=self)
        self.status_freq_label.setStyleSheet(_ss + " font-weight: bold;")
        self.status_freq_label.move(sx + self.status_auto_cb.width() + 2, sy)
        self.status_freq_label.adjustSize()

        self.status_freq_spin = QDoubleSpinBox(parent=self)
        self.status_freq_spin.setRange(0.1, 20.0)
        self.status_freq_spin.setSingleStep(0.5)
        self.status_freq_spin.setValue(1.0)
        self.status_freq_spin.setDecimals(1)
        self.status_freq_spin.resize(65, 24)
        self.status_freq_spin.move(sx, sy + 22)
        self.status_hz_label = QLabel("Hz", parent=self)
        self.status_hz_label.setStyleSheet(_ss)
        self.status_hz_label.move(sx + 68, sy + 26)
        self.status_hz_label.adjustSize()

        self.ask_status_btn = QPushButton("Ask for Status", parent=self)
        self.ask_status_btn.setStyleSheet(_btn_ss)
        self.ask_status_btn.resize(sidebar_w, 26)
        self.ask_status_btn.move(sx, sy + 50)
        self.ask_status_btn.clicked.connect(self.ros_node.request_status)
        self.ask_status_btn.show()

        # --- Torque section ---
        ty = sy + 88
        self.torque_auto_cb = QCheckBox("Auto", parent=self)
        self.torque_auto_cb.setStyleSheet(_cb_ss)
        self.torque_auto_cb.move(sx, ty)
        self.torque_auto_cb.adjustSize()
        self.torque_freq_label = QLabel("Torque Frequency", parent=self)
        self.torque_freq_label.setStyleSheet(_ss + " font-weight: bold;")
        self.torque_freq_label.move(sx + self.torque_auto_cb.width() + 2, ty)
        self.torque_freq_label.adjustSize()

        self.torque_freq_spin = QDoubleSpinBox(parent=self)
        self.torque_freq_spin.setRange(0.1, 20.0)
        self.torque_freq_spin.setSingleStep(0.5)
        self.torque_freq_spin.setValue(1.0)
        self.torque_freq_spin.setDecimals(1)
        self.torque_freq_spin.resize(65, 24)
        self.torque_freq_spin.move(sx, ty + 22)
        self.torque_hz_label = QLabel("Hz", parent=self)
        self.torque_hz_label.setStyleSheet(_ss)
        self.torque_hz_label.move(sx + 68, ty + 26)
        self.torque_hz_label.adjustSize()

        self.ask_torque_btn = QPushButton("Ask for Torque", parent=self)
        self.ask_torque_btn.setStyleSheet(_btn_ss)
        self.ask_torque_btn.resize(sidebar_w, 26)
        self.ask_torque_btn.move(sx, ty + 50)
        self.ask_torque_btn.clicked.connect(self.ros_node.request_torque_status)
        self.ask_torque_btn.show()

        # wire checkbox + spinbox changes
        self.status_auto_cb.toggled.connect(self._on_status_auto_toggled)
        self.status_freq_spin.valueChanged.connect(self._on_status_freq_changed)
        self.torque_auto_cb.toggled.connect(self._on_torque_auto_toggled)
        self.torque_freq_spin.valueChanged.connect(self._on_torque_freq_changed)
        # also persist changes
        self.status_auto_cb.toggled.connect(self._save_poll_settings)
        self.status_freq_spin.valueChanged.connect(self._save_poll_settings)
        self.torque_auto_cb.toggled.connect(self._save_poll_settings)
        self.torque_freq_spin.valueChanged.connect(self._save_poll_settings)
        # load saved settings (must happen after widgets exist and are wired)
        self._load_poll_settings()
        # Step control slider + spinbox — placed below the freq controls in the sidebar
        _ctrl_y = ty + 116   # just below "Ask for Torque" button (ty+50+26+10)
        self.step_label = QLabel(f"Step: {self.step}", parent=self)
        self.step_slider = QSlider(Qt.Orientation.Horizontal, parent=self)
        self.step_slider.setRange(0, 90)
        self.step_slider.setValue(self.step)
        self.step_spinBox = QSpinBox(parent=self)
        self.step_spinBox.setRange(0, 90)
        self.step_spinBox.setValue(self.step)
        self.step_label.move(sx, _ctrl_y)
        self.step_slider.move(sx, _ctrl_y + 20)
        self.step_slider.resize(sidebar_w - 42, 20)
        self.step_spinBox.move(sx + sidebar_w - 40, _ctrl_y + 16)
        self.step_spinBox.resize(40, 22)
        # Warning label (hidden behind step_label; shown on bad input)
        self.step_warning = QLabel("Step Size, Max angle is 90", parent=self)
        self.step_warning.setStyleSheet("color: red; font-weight: bold;")
        self.step_warning.move(sx, _ctrl_y - 14)
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
        self.action_time = 1000
        self.action_time_label = QLabel("Action Time", parent=self)
        self.action_time_label.setStyleSheet("color: black; background-color: white; font-weight: bold;")
        self.action_time_label.adjustSize()
        self.action_time_spinBox = QSpinBox(parent=self)
        self.action_time_spinBox.setRange(200, 2856)
        self.action_time_spinBox.setValue(self.action_time)
        self.action_time_label.move(sx, _ctrl_y + 48)
        self.action_time_spinBox.move(sx + sidebar_w - 80, _ctrl_y + 44)
        self.action_time_spinBox.resize(80, 22)
        # Clear Errors button — below action time
        self.error_clear_btn.resize(sidebar_w, 30)
        self.error_clear_btn.move(sx, _ctrl_y + 76)
        # Reinitialize button — reboots all servos then runs initialize() on STM
        if not hasattr(self, 'reinit_btn'):
            self.reinit_btn = QPushButton("Reinitialize", parent=self)
            self.reinit_btn.setStyleSheet(
                "QPushButton { background: #2980b9; color: white; font-weight: bold; "
                "font-size: 13px; border-radius: 4px; padding: 4px; }\n"
                "QPushButton:pressed { background: #1a5276; }")
            self.reinit_btn.clicked.connect(self.ros_node.reinitialize_servos)
            self.reinit_btn.show()
        self.reinit_btn.resize(sidebar_w, 30)
        self.reinit_btn.move(sx, _ctrl_y + 112)
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
        """Unpack nubi_response status payload: servo n -> error=data[2n], detail=data[2n+1].
        Standard (non-Herkulex) servos are excluded — they have no status register."""
        for servo_id, widget in self.servo_control_subWidgets_dict.items():
            if servo_id in STD_SERVO_IDS:
                continue  # not a Herkulex servo — no status to read
            err_idx = 2 * servo_id
            det_idx = 2 * servo_id + 1
            if det_idx < len(data):
                widget.set_status(data[err_idx], data[det_idx])

    #ros node subscribe callbacks
    def handle_angles_callback(self, name:str, angles_list:list[int]):
        ids = all_commands_dict[name].ids_array
        for i, id in enumerate(ids):
            if id in STD_SERVO_IDS:
                continue  # std servos have no position feedback from STM
            if i >= len(angles_list):
                break
            self.servo_control_subWidgets_dict[id].set_angle(angles_list[i])

    def _torque_verify_tick(self):
        """Poll torque status once per second, up to 5 times after a torque toggle."""
        if self._torque_verify_count <= 0:
            self._torque_verify_timer.stop()
            return
        self.ros_node.request_torque_status()
        self._torque_verify_count -= 1
        if self._torque_verify_count <= 0:
            self._torque_verify_timer.stop()
            # Give 1 extra second for the last response to arrive
            self._torque_timeout_timer.start()

    def _torque_verify_timeout(self):
        """Called 1 s after the 5th poll. If we didn't get all 5 responses, reset to None."""
        if self._torque_response_count < 5:
            print(f"Torque verification failed: only {self._torque_response_count}/5 responses received. Resetting to None.")
            self.torque_lock_widget.set_torque_state(None)

    def handle_torque_feedback(self, torque_list: list):
        """Handle torque feedback (list of 20 ints 0/1) from status_response."""
        if not torque_list:
            return
        self._torque_response_count += 1
        # Use servo 0 as representative state (all servos toggled together)
        torque_bool = bool(torque_list[0])
        self.torque_lock_widget.set_torque_state(torque_bool)
        # Update each servo subwidget's individual torque indicator
        for servo_id, widget in self.servo_control_subWidgets_dict.items():
            if servo_id < len(torque_list):
                widget.set_torque(bool(torque_list[servo_id]))

    def check_torque_timeout(self):
        # Replaced by polling; kept as no-op for compatibility
        pass

    # ── Sidebar polling control handlers ──────────────────────────────────────
    def _on_status_auto_toggled(self, checked: bool):
        if checked:
            ms = max(50, int(1000 / self.status_freq_spin.value()))
            self._status_poll_timer.start(ms)
        else:
            self._status_poll_timer.stop()

    def _on_status_freq_changed(self, hz: float):
        if self.status_auto_cb.isChecked():
            ms = max(50, int(1000 / hz))
            self._status_poll_timer.start(ms)

    def _on_torque_auto_toggled(self, checked: bool):
        if checked:
            ms = max(50, int(1000 / self.torque_freq_spin.value()))
            self._torque_poll_timer.start(ms)
        else:
            self._torque_poll_timer.stop()

    def _on_torque_freq_changed(self, hz: float):
        if self.torque_auto_cb.isChecked():
            ms = max(50, int(1000 / hz))
            self._torque_poll_timer.start(ms)

    def _save_poll_settings(self, *_):
        if getattr(self, "_loading_settings", False):
            return
        s = QSettings("NUBI", "ServoGUI")
        s.setValue("status_auto", int(self.status_auto_cb.isChecked()))
        s.setValue("status_hz", self.status_freq_spin.value())
        s.setValue("torque_auto", int(self.torque_auto_cb.isChecked()))
        s.setValue("torque_hz", self.torque_freq_spin.value())
        s.sync()

    def _load_poll_settings(self):
        self._loading_settings = True
        try:
            s = QSettings("NUBI", "ServoGUI")
            # Restore frequency values first (before toggling auto, so timers start with correct interval)
            status_hz = float(s.value("status_hz", 1.0))
            torque_hz = float(s.value("torque_hz", 1.0))
            self.status_freq_spin.setValue(status_hz)
            self.torque_freq_spin.setValue(torque_hz)
            # Restore checkbox states — stored as int 0/1 for reliability
            def _to_bool(val):
                if isinstance(val, str):
                    return val.strip().lower() in ("1", "true")
                return bool(int(val))
            status_auto = _to_bool(s.value("status_auto", 0))
            torque_auto = _to_bool(s.value("torque_auto", 0))
            self.status_auto_cb.setChecked(status_auto)
            self.torque_auto_cb.setChecked(torque_auto)
        finally:
            self._loading_settings = False

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

    def _send_torque(self, new_state: bool):
        self.torque_lock_widget.turn_blue()   # visual feedback: request sent
        self.ros_node.publish_torque(new_state)
        print(f"Torque Lock: {new_state}")
        # Reset counts and start verification: poll 5 times, once per second
        self._torque_verify_count = 5
        self._torque_response_count = 0
        self._torque_timeout_timer.stop()
        self._torque_verify_timer.start()

    def toggle_torque(self):
        new_state = not self.torque_lock_widget.torque_lock_status
        self._send_torque(new_state)

    def set_torque_on(self):
        self._send_torque(True)

    def set_torque_off(self):
        self._send_torque(False)

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
        if servo_widget.id in STD_SERVO_IDS:
            new_servo_angle = max(0, min(180, new_servo_angle))
        else:
            new_servo_angle = max(-SERVO_ANGLE_LIMIT, min(SERVO_ANGLE_LIMIT, new_servo_angle))
        all_angles[servo_index] = new_servo_angle
        # std servos have no position feedback — assume they reached the commanded angle
        if servo_widget.id in STD_SERVO_IDS:
            servo_widget.set_angle(new_servo_angle)

        # Herkulex servos: move only this one servo via CMD_MOVE_ONE (index 8)
        # STD servos still need the full array published on their topic
        if servo_widget.id not in STD_SERVO_IDS:
            self.ros_node.move_one_servo(
                servo_widget.id,
                new_servo_angle,
                getattr(self, 'action_time', 500)
            )
            print(f"move_one_servo id={servo_widget.id} angle={new_servo_angle}")
            return

        pub_topic = getattr(command, 'pub_topic', None)
        pub_type = getattr(command, 'pub_type', None)
        if not pub_topic or not pub_type:
            print(f"Command '{command.name}' has no publisher info (pub_topic/pub_type); cannot publish")
            return

        msg = pub_type()
        msg.data = all_angles + [getattr(self, 'action_time', 1000)]
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