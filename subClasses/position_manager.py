import json
import os

from PyQt6.QtGui import QPixmap

# ─── Widget size constants ────────────────────────────────────────────────────
font_size         = 18
servo_widget_width = 95

# ─── JSON path ────────────────────────────────────────────────────────────────
_POSITIONS_JSON = os.path.join(os.path.dirname(__file__), "servo_positions.json")

# ─── Defaults ────────────────────────────────────────────────────────────────
_sw = servo_widget_width
_shift3, _shift4, _shift5 = 79, 164, 127
_shift11, _shift12        = 330, 60
_shift17, _shift19        = 45, 18

DEFAULT_X_SHIFTS: dict[int, int] = {
    0:  -_shift3  - _sw,  1:  -_shift4  - _sw,  2:  -_shift5  - _sw,
    3:  +_shift3,          4:  +_shift4,          5:  +_shift5,
    6:  -_shift11 - _sw,  7:  -_shift12 - _sw,  8:  -_shift12 - _sw,
    9:  -_shift12 - _sw,  10: -_shift11 - _sw,  11: +_shift11,
    12: +_shift12,          13: +_shift12,         14: +_shift12,
    15: +_shift11,          16: -_shift17 - _sw,  17: +_shift17,
    18: +_shift5,           19: +_shift19,
    # Standard (non-Herkulex) servos S1-S4
    101: +_shift5 + 20,    102: +_shift5 + 20,
    103: -(_shift5 + 20) - _sw,  104: -(_shift5 + 20) - _sw,
}

DEFAULT_Y_VALUES: dict[int, int] = {
    0:  140,  1:  136,  2:  260,  3:  140,  4:  136,  5:  260,
    6:  310,  7:  345,  8:  435,  9:  525,  10: 510,
    11: 310,  12: 345,  13: 435,  14: 525,  15: 510,
    16: 255,  17: 255,  18: 260,  19: 175,
    # Standard servos S1-S4
    101: 345,  102: 435,  103: 345,  104: 435,
}

# ─── Linkage groups ───────────────────────────────────────────────────────────
X_SHIFT_GROUPS: list[list[int]] = [
    [0], [1], [2], [3], [4], [5, 18], [6, 10], [7, 8, 9],
    [11, 15], [12, 13, 14], [16], [17], [19], [101], [102], [103], [104],
]

Y_GROUPS: list[list[int]] = [
    [0, 3], [1, 4], [2, 5, 18], [6, 11], [7, 12],
    [8, 13], [9, 14], [10, 15], [16, 17], [19], [101], [102], [103], [104],
]

X_GROUP_FOR_ID: dict[int, list[int]] = {}
for _grp in X_SHIFT_GROUPS:
    for _sid in _grp:
        X_GROUP_FOR_ID[_sid] = _grp

Y_GROUP_FOR_ID: dict[int, list[int]] = {}
for _grp in Y_GROUPS:
    for _sid in _grp:
        Y_GROUP_FOR_ID[_sid] = _grp


# ─── Load / Save ──────────────────────────────────────────────────────────────
def load_servo_positions() -> tuple[dict[int, int], dict[int, int]]:
    if os.path.isfile(_POSITIONS_JSON):
        try:
            with open(_POSITIONS_JSON, "r") as f:
                data = json.load(f)
            x_shifts = {int(k): v for k, v in data["x_shifts"].items()}
            y_values = {int(k): v for k, v in data["y_values"].items()}
            return x_shifts, y_values
        except Exception as e:
            print(f"[servo_positions] Failed to load: {e}. Using defaults.")
    return dict(DEFAULT_X_SHIFTS), dict(DEFAULT_Y_VALUES)


def save_servo_positions(x_shifts: dict[int, int], y_values: dict[int, int]) -> None:
    try:
        with open(_POSITIONS_JSON, "w") as f:
            json.dump({"x_shifts": {str(k): v for k, v in x_shifts.items()},
                       "y_values": {str(k): v for k, v in y_values.items()}}, f, indent=2)
    except Exception as e:
        print(f"[servo_positions] Failed to save: {e}")


# ─── Position helper ──────────────────────────────────────────────────────────
def return_servo_subWidgets_positions(bg: QPixmap) -> dict[int, tuple[int, int]]:
    """Return absolute (x, y) widget positions, loading from JSON or defaults."""
    from subClasses.servo_widget import servo_control_subWidget
    centerx = int(bg.size().width() / 2) - 15
    servo_control_subWidget.width = servo_widget_width
    x_shifts, y_values = load_servo_positions()
    return {i: (centerx + x_shifts[i], y_values[i]) for i in x_shifts}
