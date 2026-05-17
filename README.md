# NUPI3

[Frames PDF](moveit_robot_arm_sim2/frames_2026-04-25_00.08.47.pdf)

## Build

```bash
colcon build
source install/setup.bash
```

## Launch RViz

```bash
ros2 launch moveit_robot_arm_sim demo.launch.py
```

## Run the Script to Enter the Coordinates

```bash
ros2 run moveit_robot_arm_sim2 move_to_xyz.py
```

## Run the Agent and the Publisher

```bash
ros2 run moveit_robot_arm_sim2 serial_bridge.py
```

```bash
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0
```
