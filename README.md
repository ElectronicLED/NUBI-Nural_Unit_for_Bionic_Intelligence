# How to run the SLAM for the robot

## Required Libraries:
These libraries are requires to be downloaded from their respective links and built
using their cmakelist
1. pandolin
NOTE: before installing orb_slam3, please replace its cmakelist.txt with the given one
2. ORB_SLAM3
3. depthai_core and depthai_python
4. opencv
5. Eigen3

# Required ROS node
Install and run colcon-build for the orbslam3_node using
colcon build --packages-select orbslam3_node

## Steps to run the SLAM:
We feed the camera output to orb slam3 using ros topics
**First**, initialize the camera ros nodes using
### ros2 launch depthai_examples stereo.launch.py
This command should work if depthai_core and depthai_python were installed correctly

**Second** we need to feed the output as an input to orb slam3
we will use the ROS node previously installed for this task
ros2 run orbslam3_node orbslam3_ros2

Theoretically that's what it takes, unfortunately many errors may happen along the way due to each external library updating itself
with no humane regard to others, causing a great deal of pain
I hope this doesn't happen though
