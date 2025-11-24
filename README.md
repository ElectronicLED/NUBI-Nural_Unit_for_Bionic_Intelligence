# How to run the SLAM for the robot

## Required Libraries:
These libraries are requires to be downloaded from their respective links and built, its recommended to download everything from source
using their cmakelist
1. pangolin: https://github.com/stevenlovegrove/Pangolin
2. Libcpr
This library gets installed automatically by the depthai prerequisites script that they will ask you to run
unfortunately they're using a broken link, so you need to manually install it to avoid running its this error<br>
Steps:<br>
git clone https://github.com/libcpr/cpr.git  
cd cpr  
git checkout 1.11.0   
mkdir build && cd build  
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON ..  
make -j$(nproc)  
sudo make install  
3. opencv: https://github.com/opencv/opencv
4. Eigen3: sudo apt install libeigen3-dev
5. depthai_core and depthai_ros<br>
both are installed from: https://docs.luxonis.com/software/ros/depthai-ros/build/
The install dependencies script will automatically install depthai-core so make sure to run it in the folder you want to install depthai-core at before moving on to installing depthai-ros<br>
and yes the install dependencies script takes very long time >30 mins and fails a lot in the middle its ok happens to the best of us
6. ORB_SLAM3<br>
NOTE: before installing orb_slam3, please replace its cmakelist.txt with the given one<br>
https://docs.luxonis.com/software/ros/depthai-ros/build/

# Required ROS node
Install and run colcon-build for the orbslam3_node using<br>
###colcon build --packages-select orbslam3_node

## Steps to run the SLAM:
We feed the camera output to orb slam3 using ros topics
**First**, initialize the camera ros nodes using
### ros2 launch depthai_examples stereo.launch.py
This command should work if depthai_core and depthai_python were installed correctly

**Second** we need to feed the output as an input to orb slam3
we will use the ROS node previously installed for this task using <br>
### ros2 run orbslam3_node orbslam3_ros2

Theoretically that's what it takes, unfortunately many errors may happen along the way due to each external library updating itself
with no humane regard to others, causing a great deal of pain<br>
I hope this doesn't happen though
