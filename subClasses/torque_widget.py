from PyQt6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, pyqtSignal


class torque_control_subWidget(QWidget):
    parent           = None
    toggle_requested = pyqtSignal()

    def __init__(self, toggle_key, name=None):
        super().__init__(torque_control_subWidget.parent)
        self.torque_lock_status = None
        self.toggle_key         = toggle_key
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("""
            QWidget { border-radius: 5px; }
            QWidget[state="green"] { background: rgb(0, 170, 0); }
            QWidget[state="red"]   { background: rgb(255, 0, 0); }
            QWidget[state="gray"]  { background: rgb(128, 128, 128); }
            QLabel      { color: white; font-size: 20px; font-weight: bold; }
            QPushButton { color: white; font-size: 20px; font-weight: bold; }
        """)
        self.setFixedWidth(170)
        self.turn_gray()

        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(3, 10, 3, 10)
        self.vlayout.setSpacing(0)

        self.torque_lock_label        = QLabel("Torque Lock")
        self.torque_lock_status_label = QLabel('None')
        self.torque_lock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.torque_lock_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.toggle_btn = QPushButton(f"Toggle with {toggle_key}", self)
        self.toggle_btn.clicked.connect(self.toggle_requested.emit)

        self.vlayout.addWidget(self.torque_lock_label)
        self.vlayout.addWidget(self.torque_lock_status_label)
        self.vlayout.addWidget(self.toggle_btn)

    # ── Colour helpers ────────────────────────────────────────────────────────
    def _set_state(self, state: str):
        self.setProperty("state", state)
        self.style().unpolish(self)
        self.style().polish(self)

    def turn_green(self): self._set_state("green")
    def turn_red(self):   self._set_state("red")
    def turn_gray(self):  self._set_state("gray")

    # ── Public API ────────────────────────────────────────────────────────────
    def set_torque_state(self, state):
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
        self.torque_lock_status = None
        self.torque_lock_status_label.setText('No reading\nreceived for\npast 5 seconds')
        self.turn_gray()
