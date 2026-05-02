from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                              QHeaderView, QSizePolicy, QAbstractItemView, QLabel)
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtCore import Qt

_STATUS_ROWS = [
    ("0x01", "Exceed Input Voltage limit", False),
    ("0x02", "Exceed allowed POT limit",   False),
    ("0x04", "Exceed Temperature limit",   False),
    ("0x08", "Invalid Packet",             True),
    ("0x10", "Overload detected",          False),
    ("0x20", "Driver fault detected",      False),
    ("0x40", "EEP REG distorted",          False),
]

_DETAIL_ROWS = [
    ("0x01", "Moving flag",      False),
    ("0x02", "Inposition flag",  False),
    ("0x04", "Checksum Error",   True),
    ("0x08", "Unknown Command",  True),
    ("0x10", "Exceed REG range", True),
    ("0x20", "Garbage detected", True),
    ("0x40", "MOTOR_ON flag",    False),
]

_COL_YELLOW  = QColor("#FFD700")
_COL_WHITE   = QColor("#FFFFFF")
_COL_BLACK   = QColor("#000000")
_TABLE_FONT_SIZE  = 11   # pt – increase here to taste
_TITLE_FONT_SIZE  = 10


def _make_cell(text: str, yellow: bool) -> QTableWidgetItem:
    item = QTableWidgetItem(text)
    item.setForeground(_COL_BLACK)
    item.setBackground(_COL_YELLOW if yellow else _COL_WHITE)
    item.setFlags(Qt.ItemFlag.ItemIsEnabled)
    f = QFont(); f.setPointSize(_TABLE_FONT_SIZE)
    item.setFont(f)
    return item


class StatusReferenceTable(QWidget):
    """Draggable combined Status + Detail reference table."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._dragging    = False
        self._drag_offset = None
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet("QWidget { background: white; border: 1px solid #aaa; border-radius: 4px; }")
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(6, 6, 6, 6)
        outer.setSpacing(4)

        title = QLabel("── Servo Status Reference ──")
        tf = QFont(); tf.setPointSize(_TITLE_FONT_SIZE); tf.setBold(True)
        title.setFont(tf)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: black; border: none;")
        outer.addWidget(title)

        table = QTableWidget(7, 4)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(True)
        table.setHorizontalHeaderLabels(["Error", "Comment", "Detail", "Comment"])

        hf = QFont(); hf.setBold(True); hf.setPointSize(_TITLE_FONT_SIZE)
        table.horizontalHeader().setFont(hf)
        table.horizontalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        table.horizontalHeader().setStyleSheet(
            "QHeaderView::section { color: black; background-color: #e0e0e0; "
            "border: 1px solid #aaa; padding: 2px; }"
        )
        # All columns resize to fit their content — no truncation
        for col in range(4):
            table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        for row, ((sv, sc, sy), (dv, dc, dy)) in enumerate(zip(_STATUS_ROWS, _DETAIL_ROWS)):
            table.setItem(row, 0, _make_cell(sv, sy))
            table.setItem(row, 1, _make_cell(sc, sy))
            table.setItem(row, 2, _make_cell(dv, dy))
            table.setItem(row, 3, _make_cell(dc, dy))

        table.resizeRowsToContents()
        table.resizeColumnsToContents()

        # Size the table widget to exactly fit its content
        total_w = (sum(table.columnWidth(c) for c in range(4))
                   + table.verticalHeader().width()
                   + table.frameWidth() * 2 + 4)
        total_h = (table.verticalHeader().length()
                   + table.horizontalHeader().height()
                   + table.frameWidth() * 2 + 4)
        table.setFixedSize(total_w, total_h)

        outer.addWidget(table)
        self.adjustSize()

    # ── Drag ─────────────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._dragging    = True
            self._drag_offset = event.position().toPoint()
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._dragging and self._drag_offset is not None:
            self.move(self.mapToParent(event.position().toPoint()) - self._drag_offset)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._dragging and event.button() == Qt.MouseButton.LeftButton:
            self._dragging    = False
            self._drag_offset = None
            event.accept()
        else:
            super().mouseReleaseEvent(event)
