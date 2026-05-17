[Frames](moveit_robot_arm_sim2/frames_2026-04-25_00.08.47.pdf)
# NUPI3
## Build
colcon build
source install/setup.bash
## launch RVIZ
ros2 launch moveit_robot_arm_sim demo.launch.py
## run the script to enter the coordinates
ros2 run moveit_robot_arm_sim2 move_to_xyz.py
## run the agent and the publisher
ros2 run moveit_robot_arm_sim2 serial_bridge.py
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0
