#!/usr/bin/env python3 

import rclpy
import threading  # <--- Import threading
from std_msgs.msg import Int16MultiArray
from std_msgs.msg import Bool
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
import time

_BE_QOS = QoSProfile(
    reliability=ReliabilityPolicy.BEST_EFFORT,
    history=HistoryPolicy.KEEP_LAST,
    depth=1
)

# Global variables to store the latest positions
legs_pos_feedback = [0,0,0,0,0,0,0,0,0,0,0,0]
upperbody_pos_feedback = [0,0,0,0,0,0,0]

def main():
    rclpy.init()
    node = rclpy.create_node("LAPTOP_NODE")

    # --- Publishers ---
    publisher_legs = node.create_publisher(Int16MultiArray,"legs_command",_BE_QOS)
    publisher_upperbody = node.create_publisher(Int16MultiArray,"upperbody_command",_BE_QOS)
    publisher_torque = node.create_publisher(Bool,"torque_command",10)

    # --- Callbacks ---
    def sub_legs_callback(msg):
        # Update global list efficiently
        legs_pos_feedback[:] = msg.data[:]

    def sub_upperbody_callback(msg):
        # Update global list efficiently
        upperbody_pos_feedback[:] = msg.data[:]

    # --- Subscribers ---
    # Using a queue size of 1 ensures we don't buffer old data if the thread lags
    node.create_subscription(Int16MultiArray, "legs_feedback", sub_legs_callback, _BE_QOS)
    node.create_subscription(Int16MultiArray, "upperbody_feedback", sub_upperbody_callback, _BE_QOS)

    # --- Helper Functions ---
    def upperbody_command(arr):
        msg = Int16MultiArray()
        msg.data = arr
        publisher_upperbody.publish(msg)
    
    def legs_command(arr):
        msg = Int16MultiArray()
        msg.data = arr
        publisher_legs.publish(msg)

    # --- START BACKGROUND THREAD ---
    # This ensures callbacks run constantly, even when input() is blocking
    spin_thread = threading.Thread(target=rclpy.spin, args=(node,), daemon=True)
    spin_thread.start()
    
    # --- Main Loop ---
    upper_acc_arr = []
    legs_acc_arr = []

    # Enable torque initially
    publisher_torque.publish(Bool(data=False)) 
    print("Torque DISABLED. Move robot to position.")

    try:
        while True:
            # This input blocks the loop, but the THREAD keeps updating the variables!
            x = input("\n[Main Loop] Press (R) to record, (P) to play, or (Q) to quit: ")

            if x.lower() == "p":
                print("Playing...")
                publisher_torque.publish(Bool(data=True)) # Enable Torque
                time.sleep(0.5) # Give servos time to stiffen
                
                for i in range(len(upper_acc_arr)):
                    upperbody_command(upper_acc_arr[i])
                    legs_command(legs_acc_arr[i])
                    print(f"Playing Step {i+1}: {upper_acc_arr[i]}")
                    print(f"Playing Step {i+1}: {legs_acc_arr[i]}")
                    
                    time.sleep(2)
                
                # Clear arrays after playing? (Optional, based on your logic)
                legs_acc_arr.clear()
                upper_acc_arr.clear()
                print("Done playing. Torque DISABLED.")
                publisher_torque.publish(Bool(data=False)) 

            elif x.lower() == "r":
                # Create a copy of the current list so we don't save a reference
                current_upperbody_pos = list(upperbody_pos_feedback)
                current_legs_pos = list(legs_pos_feedback)
                upper_acc_arr.append(current_upperbody_pos)
                legs_acc_arr.append(current_legs_pos)
                
                print("Recorded Frame!")
                print(f"Captured: {current_upperbody_pos}")

            elif x.lower() == "q":
                break
                
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()