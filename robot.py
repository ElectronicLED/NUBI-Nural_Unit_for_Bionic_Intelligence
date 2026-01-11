import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool,Int16MultiArray
import json
import time

filename = "data.json"

with open(filename, "r") as f:
    data = json.load(f)

rclpy.init()
node = rclpy.create_node("LAPTOP_NODE")

# --- Publishers ---
publisher_legs = node.create_publisher(Int16MultiArray,"legs_command",10)
publisher_upperbody = node.create_publisher(Int16MultiArray,"upperbody_command",10)
#publisher_torque = node.create_publisher(Bool,"torque_command",10)



def default_stance():
    upper_cmd =  Int16MultiArray()
    lower_cmd = Int16MultiArray()
    upper_cmd.data = data["default"]["upper_body"]
    lower_cmd.data = data["default"]["lower_body"]

    publisher_upperbody.publish(upper_cmd)
    time.sleep(0.1)
    publisher_legs.publish(lower_cmd)

def fight_stance():
    upper_cmd =  Int16MultiArray()
    lower_cmd = Int16MultiArray()
    upper_cmd.data = data["fight0"]["upper_body"]
    lower_cmd.data = data["fight0"]["lower_body"]

    publisher_upperbody.publish(upper_cmd)
    time.sleep(0.2)
    publisher_legs.publish(lower_cmd)


def jab():
    fight_stance()
    time.sleep(0.5)
    upper_cmd =  Int16MultiArray()
    lower_cmd = Int16MultiArray()
    upper_cmd.data = data["jab"]["upper_body"]
    lower_cmd.data = data["jab"]["lower_body"]

    publisher_upperbody.publish(upper_cmd)
    time.sleep(0.1)
    publisher_legs.publish(lower_cmd)

    time.sleep(1.5)

    fight_stance()

def cross():
    fight_stance()
    time.sleep(0.5)
    upper_cmd =  Int16MultiArray()
    lower_cmd = Int16MultiArray()
    upper_cmd.data = data["cross"]["upper_body"]
    lower_cmd.data = data["cross"]["lower_body"]
    publisher_upperbody.publish(upper_cmd)
    time.sleep(0.1)
    publisher_legs.publish(lower_cmd)
    time.sleep(1.8)
    fight_stance()

def wave(i=1):
    default_stance()
    time.sleep(0.5)
    upper_cmd =  Int16MultiArray()
    lower_cmd = Int16MultiArray()
    upper_cmd.data = data["wave0"]["upper_body"]
    publisher_upperbody.publish(upper_cmd)
    time.sleep(0.5)

    while i>0:
        #wave center
        upper_cmd.data = data["wave1"]["upper_body"]
        publisher_upperbody.publish(upper_cmd)
        time.sleep(0.5)
        upper_cmd.data = data["wave0"]["upper_body"]
        publisher_upperbody.publish(upper_cmd)
        time.sleep(0.5)
        upper_cmd.data = data["wave1"]["upper_body"]
        publisher_upperbody.publish(upper_cmd)
        time.sleep(0.5)
        upper_cmd.data = data["wave0"]["upper_body"]
        publisher_upperbody.publish(upper_cmd)
        time.sleep(0.5)

        #wave right
        lower_cmd.data = data["wave0"]["lower_body"]
        publisher_legs.publish(lower_cmd)
        upper_cmd.data = data["wave1"]["upper_body"]
        publisher_upperbody.publish(upper_cmd)
        time.sleep(0.5)
        upper_cmd.data = data["wave0"]["upper_body"]
        publisher_upperbody.publish(upper_cmd)
        time.sleep(0.5)
        upper_cmd.data = data["wave1"]["upper_body"]
        publisher_upperbody.publish(upper_cmd)
        time.sleep(0.5)

        upper_cmd.data = data["wave0"]["upper_body"]
        publisher_upperbody.publish(upper_cmd)
        time.sleep(0.5)

        #wave left
        lower_cmd.data = data["wave1"]["lower_body"]
        publisher_legs.publish(lower_cmd)

        upper_cmd.data = data["wave1"]["upper_body"]
        publisher_upperbody.publish(upper_cmd)
        time.sleep(0.5)

        upper_cmd.data = data["wave0"]["upper_body"]
        publisher_upperbody.publish(upper_cmd)
        time.sleep(0.5)

        upper_cmd.data = data["wave1"]["upper_body"]
        publisher_upperbody.publish(upper_cmd)
        time.sleep(0.5)

        upper_cmd.data = data["wave0"]["upper_body"]
        publisher_upperbody.publish(upper_cmd)
        time.sleep(0.5)

        i-=1
    
    default_stance()

def squat():
    default_stance()
    time.sleep(0.5)
    upper_cmd =  Int16MultiArray()
    lower_cmd = Int16MultiArray()
    lower_cmd.data = data["squat0"]["lower_body"]
    publisher_legs.publish(lower_cmd)
    time.sleep(1.5)
    lower_cmd.data = data["squat1"]["lower_body"]
    publisher_legs.publish(lower_cmd)
    time.sleep(1.5)
    lower_cmd.data = data["squat2"]["lower_body"]
    publisher_legs.publish(lower_cmd)
    time.sleep(1.5)
    lower_cmd.data = data["squat3"]["lower_body"]
    publisher_legs.publish(lower_cmd)
    time.sleep(1.5)
    lower_cmd.data = data["squat2"]["lower_body"]
    publisher_legs.publish(lower_cmd)
    time.sleep(1.5)
    lower_cmd.data = data["squat1"]["lower_body"]
    publisher_legs.publish(lower_cmd)
    time.sleep(2)
    lower_cmd.data = data["squat0"]["lower_body"]
    publisher_legs.publish(lower_cmd)
    time.sleep(2)
    default_stance()





default_stance()
time.sleep(1)
wave(2)
default_stance()
time.sleep(1)
fight_stance()
time.sleep(1)
jab()
time.sleep(1)
cross()
time.sleep(1)
default_stance()
time.sleep(2)
