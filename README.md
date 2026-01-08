## 1. Prerequisites
### 1.1 PyQt6
`pip install PyQt6`
### 1.2 libxcb-cursor0
`sudo apt install libxcb-cursor0`

## Running camera_ros_handler

First you must run

`ros2 launch depthai_examples yolov4_publisher.launch.py spatial_camera:=true` 

then run the python file and it should start outputting the detections when they're detected