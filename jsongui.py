import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QInputDialog, QMessageBox,
    QSizePolicy
)
from PyQt6.QtGui import QFont, QFontMetrics
import json
from collections import defaultdict
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool,Int16MultiArray
import time
import re

def inline_lists(json_text):
    pattern = re.compile(
        r"\[\s*(?:-?\d+(?:\.\d+)?(?:,\s*)?)+\s*\]",
        re.MULTILINE
    )

    def replacer(match):
        nums = re.findall(r"-?\d+(?:\.\d+)?", match.group())
        return "[" + ", ".join(nums) + "]"

    return pattern.sub(replacer, json_text)


class jsonGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.main_vlayout = QVBoxLayout()
        self.filename = "data.json"
        self.load_data()
        # delay between actions when doing "Do All"
        self.do_all_delay = 1.3
        self.initLayout()
        self.node = rclpy.create_node("jsonGUI")
        # Start a dedicated spin thread for this node so the class is self-contained
        self.ros_thread = threading.Thread(
            target=ros_spin,
            args=(self.node,),
            daemon=True
        )
        self.ros_thread.start()
        # --- Publishers ---
        self.publisher_legs = self.node.create_publisher(Int16MultiArray,"legs_command",10)
        self.publisher_upperbody = self.node.create_publisher(Int16MultiArray,"upperbody_command",10)
        self.legs_sub = self.node.create_subscription(
            Int16MultiArray,
            "legs_feedback",
            self.legs_feedback_callback,
            10
        )
        self.arms_sub = self.node.create_subscription(
            Int16MultiArray,
            "upperbody_feedback",
            self.arms_feedback_callback,
            10
        )

    def legs_feedback_callback(self,angles_list:Int16MultiArray):
        # Always update so current_legs_angles reflects live state including 999 sentinels.
        # Recording is blocked in read_positions() if any sentinel is present.
        self.current_legs_angles = list(angles_list.data)

    def arms_feedback_callback(self,angles_list:Int16MultiArray):
        self.current_arms_angles = list(angles_list.data)

    def initLayout(self):
        # Reduce overall spacing to minimize clutter
        self.main_vlayout.setSpacing(2)
        self.main_vlayout.setContentsMargins(2, 2, 2, 2)
        self.current_arms_angles = [0, 0, 0, 0, 0, 0, 0]
        self.current_legs_angles = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.action_time = 1000  # ms default when running standalone
        self.action_time_source = None  # callable set by parent GUI to provide live action time
        self.refresh_gui()
        # Big "+" button at the end to create a new main action
        self.setLayout(self.main_vlayout)
        
    def refresh_gui(self):
        """Rebuilds the GUI based on current self.sequences"""
        # First, clear everything in layout
        while self.main_vlayout.count():
            child = self.main_vlayout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

        for seq_name, items in self.sequences.items():
            # Sequence label with a "Record Sub-action" button
            seq_layout = QHBoxLayout()
            seq_layout.setSpacing(4)
            seq_layout.setContentsMargins(0, 0, 0, 0)
            # collapse/expand toggle button
            collapsed = self.collapsed.get(seq_name, True)
            toggle_text = "v" if collapsed else "^"
            toggle_btn = QPushButton(toggle_text)
            toggle_btn.setFixedWidth(28)
            toggle_btn.clicked.connect(lambda checked, s=seq_name: self.toggle_collapse(s))
            # Do All button to perform every sub-action in sequence
            do_all_btn = QPushButton("Do All")
            do_all_btn.setFixedWidth(64)
            do_all_btn.clicked.connect(lambda checked, s=seq_name: self.do_all(s))
            seq_layout.addWidget(do_all_btn)
            seq_layout.addWidget(toggle_btn)
            seq_label = QLabel(seq_name)
            seq_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            seq_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            _f = QFont(); _f.setBold(True); _f.setPointSize(14)
            seq_label.setMinimumWidth(QFontMetrics(_f).horizontalAdvance(seq_name) + 12)

            record_sub_btn = QPushButton("Record Sub-action")
            record_sub_btn.clicked.connect(lambda checked, s=seq_name: self.add_sub_action(s))
            
            seq_layout.addWidget(seq_label)
            seq_layout.addWidget(record_sub_btn)
            self.main_vlayout.addLayout(seq_layout)

            # Add existing sub-actions
            if not self.collapsed.get(seq_name, True):
                for item in items:
                    item_layout = QHBoxLayout()
                    item_layout.setSpacing(2)
                    item_layout.setContentsMargins(8, 0, 0, 0)

                    index_label = QLabel(item[-1])

                    do_button = QPushButton("Do")
                    do_button.clicked.connect(lambda checked, k=item: self.do_action(k))

                    item_layout.addWidget(index_label)
                    item_layout.addWidget(do_button)

                    self.main_vlayout.addLayout(item_layout)

        add_main_btn = QPushButton("+ New Action")
        add_main_btn.clicked.connect(self.add_new_action)
        # Save button below everything
        save_btn = QPushButton("💾 Save Changes")
        save_btn.clicked.connect(self.save_changes)

        self.main_vlayout.addWidget(add_main_btn)
        self.main_vlayout.addWidget(save_btn)

    def save_changes(self):
        try:
            # 1) Serialize ONCE
            json_text = json.dumps(self.data, indent=4)

            # 2) Inline lists (still just text)
            json_text = inline_lists(json_text)

            # 3) Save ONCE
            with open(self.filename, "w") as f:
                f.write(json_text)

            QMessageBox.information(self, "Saved", "All changes saved successfully!")
            print("Data saved to", self.filename)

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save data: {e}")
            print("Failed to save:", e)

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())


    def toggle_collapse(self, seq_name):
        """Toggle collapsed state for a sequence and refresh GUI."""
        self.collapsed[seq_name] = not self.collapsed.get(seq_name, True)
        self.refresh_gui()


    def do_all(self, seq_name):
        """Perform every sub-action in `seq_name` in order with delay between them."""
        items = self.sequences.get(seq_name, [])
        for item in items:
            try:
                self.do_action(item)
            except Exception as e:
                print(f"Error performing {item}: {e}")
            time.sleep(self.do_all_delay)


    def load_data(self):
        with open(self.filename, "r") as f:
            self.data = json.load(f)
        
        # Group sequences
        self.sequences = defaultdict(list)
        for key in self.data.keys():
            if key[-1].isdigit():  # sequences like wave0, wave1
                base = ''.join(filter(lambda c: not c.isdigit(), key))
                self.sequences[base].append(key)
            else:  # single items like 'default', 'jab', etc.
                self.sequences[key].append(key+'0')  # append 0 to keep same format
        # Sort items in each sequence
        for k in self.sequences:
            self.sequences[k] = sorted(self.sequences[k])
        # Initialize collapsed state for sequences (default: collapsed)
        existing = getattr(self, 'collapsed', {}) if hasattr(self, 'collapsed') else {}
        self.collapsed = {k: existing.get(k, True) for k in self.sequences}

    def do_action(self, item_name):
        # Extract the base name (without trailing number) if needed
        base_name = ''.join(filter(lambda c: not c.isdigit(), item_name))
        # Some items in sequences have the trailing 0 added artificially, adjust
        json_key = item_name if item_name in self.data else base_name
        pose = self.data[json_key]
        upper = list(pose['upper_body'])   # 7 Herkulex angles
        lower = list(pose['lower_body'])   # 12 leg angles
        # Use per-pose action_time if stored, otherwise use live source or fallback default
        default_t = self.action_time_source() if callable(self.action_time_source) else self.action_time
        t = int(pose.get('action_time', default_t))
        # STM upperbody_command expects 12 elements:
        #   [0..6] = Herkulex angles, [7..10] = std servo angles (0 = no change), [11] = playtime
        # STM legs_command expects 13 elements:
        #   [0..11] = leg angles, [12] = playtime
        upper_cmd = Int16MultiArray()
        lower_cmd = Int16MultiArray()
        upper = upper + [90, 90, 90, 90, t]
        lower = lower + [t] 
        upper_cmd.data = upper    # pad 4 std-servo slots + playtime
        lower_cmd.data = lower                # append playtime
        print(f"Action: {json_key}  (t={t}ms)")
        print("Upper Body:", upper)
        print("Lower Body:", lower)

        self.publisher_upperbody.publish(upper_cmd)
        time.sleep(0.1)
        self.publisher_legs.publish(lower_cmd)

    def read_positions(self):
        """
        Returns a dict like {'upper_body': [...], 'lower_body': [...]}, or None if
        any angle is a checksum-error sentinel (abs >= 900 == STM reported bad read).
        """
        arms = list(self.current_arms_angles)
        legs = list(self.current_legs_angles)
        # 999 is the sentinel value produced when getPosition() fails checksum on the STM.
        if any(abs(v) >= 900 for v in arms) or any(abs(v) >= 900 for v in legs):
            QMessageBox.warning(
                self,
                "Checksum Error",
                "Cannot save position — one or more servo angles contain a checksum error (value ≥ 900).\n"
                "Wait for valid readings before recording."
            )
            return None
        dic = {'upper_body': arms, 'lower_body': legs}
        print(f"Saved {dic}")
        return dic

    def add_sub_action(self, seq_name):
        """Record current positions and add as a new sub-action to existing sequence"""
        positions = self.read_positions()
        if positions is None:
            return  # checksum error — dialog already shown by read_positions()
        existing_items = self.sequences[seq_name]
        new_index = str(len(existing_items))  # next sub-action index
        new_item_name = seq_name + new_index

        # Save in data
        self.data[new_item_name] = positions
        self.sequences[seq_name].append(new_item_name)
        self.sequences[seq_name] = sorted(self.sequences[seq_name])
        # ensure collapsed state exists for this sequence
        if seq_name not in self.collapsed:
            self.collapsed[seq_name] = True
        self.refresh_gui()
        print(f"Added sub-action {new_item_name} to {seq_name}")

    def add_new_action(self):
        """Create new main action with name input and first sub-action as current positions"""
        name, ok = QInputDialog.getText(self, "New Action", "Enter action name:")
        if ok and name:
            if name in self.sequences:
                QMessageBox.warning(self, "Error", "Action already exists!")
                return
            # Read positions — may return None if checksum sentinels are present
            positions = self.read_positions()
            if positions is None:
                return  # checksum error — dialog already shown by read_positions()
            sub_action_name = name + "0"
            self.data[sub_action_name] = positions
            self.sequences[name] = [sub_action_name]
            # initialize collapsed state for the new sequence
            self.collapsed[name] = True
            self.refresh_gui()
            print(f"Created new action {name} with sub-action 0")

def ros_spin(node):
    """Spin a single-threaded executor for the given node.

    Using a per-node executor avoids conflicts from multiple calls to
    rclpy.spin() sharing internal generators.
    """
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
    app = QApplication([])
    window = jsonGUI()
    window.show()
    app.exec()
    try:
        window.node.destroy_node()
    except Exception:
        pass
    try:
        rclpy.shutdown()
    except Exception:
        pass
