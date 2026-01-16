import threading
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QInputDialog, QMessageBox
)
import json
from collections import defaultdict
import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool,Int16MultiArray
import time

def make_lists_inline(obj):
    """Recursively convert lists to compact JSON strings"""
    if isinstance(obj, list):
        return json.dumps(obj, separators=(', ', ': '))  # inline array
    elif isinstance(obj, dict):
        return {k: make_lists_inline(v) for k, v in obj.items()}
    else:
        return obj


class jsonGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout()
        self.filename = "data.json"
        self.load_data()
        self.initLayout()
        self.node = rclpy.create_node("jsonGUI")
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
        self.current_legs_angles = angles_list.data
    
    def arms_feedback_callback(self,angles_list:Int16MultiArray):
        self.current_arms_angles = angles_list.data

    def initLayout(self):
        self.main_layout.setSpacing(10)
        self.current_arms_angles = [0, 0, 0, 0, 0, 0, 0]
        self.current_legs_angles = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.refresh_gui()
        # Big "+" button at the end to create a new main action
        self.setLayout(self.main_layout)
        
    def refresh_gui(self):
        """Rebuilds the GUI based on current self.sequences"""
        # First, clear everything in layout
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self.clear_layout(child.layout())

        for seq_name, items in self.sequences.items():
            # Sequence label with a "Record Sub-action" button
            seq_layout = QHBoxLayout()
            seq_label = QLabel(seq_name)
            seq_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            seq_layout.addWidget(seq_label)

            record_sub_btn = QPushButton("Record Sub-action")
            record_sub_btn.clicked.connect(lambda checked, s=seq_name: self.add_sub_action(s))
            seq_layout.addWidget(record_sub_btn)
            self.main_layout.addLayout(seq_layout)

            # Add existing sub-actions
            for item in items:
                item_layout = QHBoxLayout()
                index_label = QLabel(item[-1])
                item_layout.addWidget(index_label)

                do_button = QPushButton("Do")
                do_button.clicked.connect(lambda checked, k=item: self.do_action(k))
                item_layout.addWidget(do_button)
                self.main_layout.addLayout(item_layout)
        add_main_btn = QPushButton("+ New Action")
        add_main_btn.clicked.connect(self.add_new_action)
        self.main_layout.addWidget(add_main_btn)
        # Save button below everything
        save_btn = QPushButton("💾 Save Changes")
        save_btn.clicked.connect(self.save_changes)
        self.main_layout.addWidget(save_btn)

    def save_changes(self):
        """Save current data to JSON file"""
        try:
            data_to_save = make_lists_inline(self.data)
            with open(self.filename, "w") as f:

                json.dump(data_to_save, f,separators=(",",": ") ,indent=4)
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

    def do_action(self, item_name):
        # Extract the base name (without trailing number) if needed
        base_name = ''.join(filter(lambda c: not c.isdigit(), item_name))
        # Some items in sequences have the trailing 0 added artificially, adjust
        json_key = item_name if item_name in self.data else base_name
        upper = self.data[json_key]['upper_body']
        lower = self.data[json_key]['lower_body']
        print(f"Action: {json_key}")
        print("Upper Body:", upper)
        print("Lower Body:", lower)
        upper_cmd =  Int16MultiArray()
        lower_cmd = Int16MultiArray()
        upper_cmd.data = upper
        lower_cmd.data = lower

        self.publisher_upperbody.publish(upper_cmd)
        time.sleep(0.1)
        self.publisher_legs.publish(lower_cmd)

    def read_positions(self):
        """
        Dummy function for now. Replace with ROS code to read current positions.
        Returns a dict like {'upper_body': [...], 'lower_body': [...]}
        """
        # Placeholder example
        dic = {
            'upper_body': list(self.current_arms_angles),
            'lower_body': list(self.current_legs_angles)
        }
        print(f"Saved {dic}")
        return dic

    def add_sub_action(self, seq_name):
        """Record current positions and add as a new sub-action to existing sequence"""
        positions = self.read_positions()
        existing_items = self.sequences[seq_name]
        new_index = str(len(existing_items))  # next sub-action index
        new_item_name = seq_name + new_index

        # Save in data
        self.data[new_item_name] = positions
        self.sequences[seq_name].append(new_item_name)
        self.sequences[seq_name] = sorted(self.sequences[seq_name])
        self.refresh_gui()
        print(f"Added sub-action {new_item_name} to {seq_name}")

    def add_new_action(self):
        """Create new main action with name input and first sub-action as current positions"""
        name, ok = QInputDialog.getText(self, "New Action", "Enter action name:")
        if ok and name:
            if name in self.sequences:
                QMessageBox.warning(self, "Error", "Action already exists!")
                return
            # Read positions
            positions = self.read_positions()
            sub_action_name = name + "0"
            self.data[sub_action_name] = positions
            self.sequences[name] = [sub_action_name]
            self.refresh_gui()
            print(f"Created new action {name} with sub-action 0")

def ros_spin(node):
    rclpy.spin(node)

if __name__ == "__main__":
    rclpy.init()
    app = QApplication([])
    window = jsonGUI()
    window.show()
    ros_thread = threading.Thread(
        target=ros_spin,
        args=(window.node,),
        daemon=True
    )
    ros_thread.start()
    app.exec()
