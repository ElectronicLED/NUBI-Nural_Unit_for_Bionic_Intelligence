from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PyQt6.QtCore import Qt, pyqtSignal

from subClasses.position_manager import font_size, servo_widget_width


class servo_control_subWidget(QWidget):
    parent = None
    width  = None
    update_angle_signal    = pyqtSignal(object, int)       # (servo_widget, sign)
    position_changed_signal = pyqtSignal(int, int, int)    # (servo_id, abs_x, abs_y)

    def __init__(self, hotkey, id, command_name: str = None, display_name: str = None):
        super().__init__(servo_control_subWidget.parent)
        self.id           = id
        self.display_name = display_name if display_name is not None else str(id)
        self.angle        = 0
        self.hotkey       = hotkey
        self.command_name = command_name
        self.name         = command_name   # ergonomic alias
        self._dragging    = False
        self._drag_offset = None
        self.initLayoutVer()

    # ── Stylesheet ────────────────────────────────────────────────────────────
    def _apply_stylesheet(self, dragging: bool = False) -> None:
        border = "2px dashed white" if dragging else "2px solid black"
        self.setStyleSheet(f"""
            QWidget {{
                background: rgba(235, 174, 52, 180);
                border: {border};
                border-radius: 8px;
            }}
            QLabel {{
                color: white;
                font-weight: bold;
                font-size: {font_size}px;
                qproperty-alignment: AlignCenter;
                background: transparent;
                border: 0px solid black;
            }}
            QPushButton {{
                color: white;
                font-weight: bold;
                font-size: {font_size}px;
                background: transparent;
                border: 2px solid black;
            }}
        """)

    # ── Layout ────────────────────────────────────────────────────────────────
    def initLayoutVer(self):
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setFixedWidth(servo_control_subWidget.width)
        self.vlayout = QVBoxLayout(self)
        self.vlayout.setContentsMargins(2, 0, 0, 0)
        self.vlayout.setSpacing(3)

        self.hotkey_label = QLabel(f"Id:{self.display_name} | {self.hotkey} ")
        self.angle_label  = QLabel("θ: None")
        self.err_label    = QLabel("err: --")
        self.det_label    = QLabel("det: --")
        self.up_btn       = QPushButton("^")
        self.down_btn     = QPushButton("v")

        self.up_btn.clicked.connect(self.increment)
        self.down_btn.clicked.connect(self.decrement)

        self.vlayout.addWidget(self.up_btn)
        self.vlayout.addWidget(self.hotkey_label)
        self.vlayout.addWidget(self.angle_label)
        self.vlayout.addWidget(self.err_label)
        self.vlayout.addWidget(self.det_label)
        self.vlayout.addWidget(self.down_btn)
        self._apply_stylesheet()

    # ── Drag ─────────────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not isinstance(self.childAt(event.position().toPoint()), QPushButton):
                self._dragging    = True
                self._drag_offset = event.position().toPoint()
                self._apply_stylesheet(dragging=True)
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_offset is not None:
            self.move(self.mapToParent(event.position().toPoint()) - self._drag_offset)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging and event.button() == Qt.MouseButton.LeftButton:
            self._dragging    = False
            self._drag_offset = None
            self._apply_stylesheet(dragging=False)
            self.position_changed_signal.emit(self.id, self.x(), self.y())
            event.accept()
            return
        super().mouseReleaseEvent(event)

    # ── Public API ────────────────────────────────────────────────────────────
    def set_status(self, err: int, det: int) -> None:
        self.err_label.setText(f"err: {err & 0xFF:#04x}")
        self.det_label.setText(f"det: {det & 0xFF:#04x}")

    def switch_sign(self):
        self.up_btn.setText(f"{'+' if self.up_btn.text()[0] == '-' else '-'} {self.hotkey}")

    def get_angle(self) -> str:
        return self.angle_label.text()[3:]

    def set_angle(self, num: int):
        if not isinstance(num, int):
            print(f"Error: angle must be int, got {type(num)}")
            return
        # 999 is the checksum-error sentinel from the STM (getPosition returns 3586
        # which maps to ~999 via the angle formula). Skip display, keep last good value.
        if abs(num) >= 900:
            return
        self.angle = num
        self.angle_label.setText(f"θ: {num}")

    def increment(self):
        self.update_angle_signal.emit(self, 1)
        print("Signal to increment servo id:", self.id)

    def decrement(self):
        self.update_angle_signal.emit(self, -1)
        print("Signal to decrement servo id:", self.id)
