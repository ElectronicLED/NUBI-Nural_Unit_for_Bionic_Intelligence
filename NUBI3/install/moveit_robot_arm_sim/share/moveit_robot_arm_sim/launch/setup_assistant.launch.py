from moveit_configs_utils import MoveItConfigsBuilder
from moveit_configs_utils.launches import generate_setup_assistant_launch


def generate_launch_description():
    moveit_config = MoveItConfigsBuilder("robot_description_3", package_name="moveit_robot_arm_sim").to_moveit_configs()
    return generate_setup_assistant_launch(moveit_config)
