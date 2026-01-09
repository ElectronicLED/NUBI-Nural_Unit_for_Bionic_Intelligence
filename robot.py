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
    upper_cmd.data = data["upper_body"]["default"]
    lower_cmd.data = data["lower_body"]["default"]

    publisher_upperbody.publish(upper_cmd)
    time.sleep(0.1)
    publisher_legs.publish(lower_cmd)

def fight_stance():
    upper_cmd =  Int16MultiArray()
    lower_cmd = Int16MultiArray()
    upper_cmd.data = data["upper_body"]["fight0"]
    lower_cmd.data = data["lower_body"]["fight0"]

    publisher_upperbody.publish(upper_cmd)
    time.sleep(0.2)
    publisher_legs.publish(lower_cmd)


def jab():
    fight_stance()
    time.sleep(0.5)
    upper_cmd =  Int16MultiArray()
    lower_cmd = Int16MultiArray()
    upper_cmd.data = data["upper_body"]["jab"]
    lower_cmd.data = data["lower_body"]["jab"]

    publisher_upperbody.publish(upper_cmd)
    time.sleep(0.1)
    publisher_legs.publish(lower_cmd)

    time.sleep(1.5)

    fight_stance()


default_stance()
time.sleep(3)
fight_stance()
time.sleep(2)
jab()