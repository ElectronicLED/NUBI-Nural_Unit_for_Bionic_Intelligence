import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool,Int16MultiArray
import json
import time

class robot_actions_controller():
    def __init__(self):
        filename = "data.json"

        with open(filename, "r") as f:
            self.data = json.load(f)
        self.node = rclpy.create_node("LAPTOP_NODE")

        # --- Publishers ---
        self.publisher_legs = self.node.create_publisher(Int16MultiArray,"legs_command",10)
        self.publisher_upperbody = self.node.create_publisher(Int16MultiArray,"upperbody_command",10)

    def default_stance(self):
        upper_cmd =  Int16MultiArray()
        lower_cmd = Int16MultiArray()
        upper_cmd.data = self.data["default"]["upper_body"]
        lower_cmd.data = self.data["default"]["lower_body"]

        self.publisher_upperbody.publish(upper_cmd)
        time.sleep(0.1)
        self.publisher_legs.publish(lower_cmd)

    def fight_stance(self):
        upper_cmd =  Int16MultiArray()
        lower_cmd = Int16MultiArray()
        upper_cmd.data = self.data["fight0"]["upper_body"]
        lower_cmd.data = self.data["fight0"]["lower_body"]

        self.publisher_upperbody.publish(upper_cmd)
        time.sleep(0.2)
        self.publisher_legs.publish(lower_cmd)


    def jab(self):
        self.fight_stance()
        time.sleep(0.5)
        upper_cmd =  Int16MultiArray()
        lower_cmd = Int16MultiArray()
        upper_cmd.data = self.data["jab"]["upper_body"]
        lower_cmd.data = self.data["jab"]["lower_body"]

        self.publisher_upperbody.publish(upper_cmd)
        time.sleep(0.1)
        self.publisher_legs.publish(lower_cmd)

        time.sleep(1.5)

        self.fight_stance()

    def cross(self):
        self.fight_stance()
        time.sleep(0.5)
        upper_cmd =  Int16MultiArray()
        lower_cmd = Int16MultiArray()
        upper_cmd.data = self.data["cross"]["upper_body"]
        lower_cmd.data = self.data["cross"]["lower_body"]
        self.publisher_upperbody.publish(upper_cmd)
        time.sleep(0.1)
        self.publisher_legs.publish(lower_cmd)
        time.sleep(1.8)
        self.fight_stance()

    def wave(self,i=1):
        self.default_stance()
        time.sleep(0.5)
        upper_cmd =  Int16MultiArray()
        lower_cmd = Int16MultiArray()
        upper_cmd.data = self.data["wave0"]["upper_body"]
        self.publisher_upperbody.publish(upper_cmd)
        time.sleep(0.5)

        while i>0:
            #wave center
            upper_cmd.data = self.data["wave1"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.5)
            upper_cmd.data = self.data["wave0"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.5)
            upper_cmd.data = self.data["wave1"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.5)
            upper_cmd.data = self.data["wave0"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.5)

            #wave right
            lower_cmd.data = self.data["wave0"]["lower_body"]
            self.publisher_legs.publish(lower_cmd)
            upper_cmd.data = self.data["wave1"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.5)
            upper_cmd.data = self.data["wave0"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.5)
            upper_cmd.data = self.data["wave1"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.5)

            upper_cmd.data = self.data["wave0"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.5)

            #wave left
            lower_cmd.data = self.data["wave1"]["lower_body"]
            self.publisher_legs.publish(lower_cmd)

            upper_cmd.data = self.data["wave1"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.5)

            upper_cmd.data = self.data["wave0"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.5)

            upper_cmd.data = self.data["wave1"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.5)

            upper_cmd.data = self.data["wave0"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.5)

            i-=1
        
        self.default_stance()

    def squat(self):
        self.default_stance()
        time.sleep(0.5)
        upper_cmd =  Int16MultiArray()
        lower_cmd = Int16MultiArray()
        lower_cmd.data = self.data["squat0"]["lower_body"]
        self.publisher_legs.publish(lower_cmd)
        time.sleep(1.5)
        lower_cmd.data = self.data["squat1"]["lower_body"]
        self.publisher_legs.publish(lower_cmd)
        time.sleep(1.5)
        lower_cmd.data = self.data["squat2"]["lower_body"]
        self.publisher_legs.publish(lower_cmd)
        time.sleep(1.5)
        lower_cmd.data = self.data["squat3"]["lower_body"]
        self.publisher_legs.publish(lower_cmd)
        time.sleep(1.5)
        lower_cmd.data = self.data["squat2"]["lower_body"]
        self.publisher_legs.publish(lower_cmd)
        time.sleep(1.5)
        lower_cmd.data = self.data["squat1"]["lower_body"]
        self.publisher_legs.publish(lower_cmd)
        time.sleep(2)
        lower_cmd.data = self.data["squat0"]["lower_body"]
        self.publisher_legs.publish(lower_cmd)
        time.sleep(2)
        self.default_stance()

    def floss(self, i=11):
        self.default_stance()
        time.sleep(0.5)
        upper_cmd =  Int16MultiArray()
        lower_cmd = Int16MultiArray()

        while i >0:
            upper_cmd.data = self.data["floss0"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.1)
            lower_cmd.data = self.data["floss0"]["lower_body"]
            self.publisher_legs.publish(lower_cmd)
            time.sleep(1.2)

            upper_cmd.data = self.data["floss1"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.1)
            lower_cmd.data = self.data["floss1"]["lower_body"]
            self.publisher_legs.publish(lower_cmd)
            time.sleep(1.2)

            upper_cmd.data = self.data["floss2"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.2)
            lower_cmd.data = self.data["floss2"]["lower_body"]
            self.publisher_legs.publish(lower_cmd)
            time.sleep(1.2)

            upper_cmd.data = self.data["floss3"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.2)
            lower_cmd.data = self.data["floss3"]["lower_body"]
            self.publisher_legs.publish(lower_cmd)
            time.sleep(1.2)

            upper_cmd.data = self.data["floss4"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.2)
            lower_cmd.data = self.data["floss4"]["lower_body"]
            self.publisher_legs.publish(lower_cmd)
            time.sleep(1.2)

            upper_cmd.data = self.data["floss3"]["upper_body"]
            self.publisher_upperbody.publish(upper_cmd)
            time.sleep(0.2)
            lower_cmd.data = self.data["floss3"]["lower_body"]
            self.publisher_legs.publish(lower_cmd)
            time.sleep(1.2)

            i-=1
        self.default_stance()






if __name__ == "__main__":
    rclpy.init()
    robot_actions_controller = robot_actions_controller()

    robot_actions_controller.default_stance()
    time.sleep(1)
    robot_actions_controller.floss(2)
    # time.sleep(1)
    # robot_actions_controller.wave(2)
    # robot_actions_controller.default_stance()
    # time.sleep(1)
    # robot_actions_controller.fight_stance()
    # time.sleep(1)
    # robot_actions_controller.jab()
    # time.sleep(1)
    # robot_actions_controller.cross()
    # time.sleep(1)
    # robot_actions_controller.default_stance()
    # time.sleep(2)
