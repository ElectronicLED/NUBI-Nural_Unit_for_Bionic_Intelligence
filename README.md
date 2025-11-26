# How to run the SLAM for the robot

# Note this whole thing assumes using ROS Humble

## Required Libraries:

These libraries are requires to be downloaded from their respective links and built, its recommended to download everything from source
using their cmakelist

### 1. Pangolin: https://github.com/stevenlovegrove/Pangolin

### 2. Libcpr<br>
This library gets installed automatically by the depthai prerequisites script that they will ask you to run  
unfortunately they're using a broken link, so you need to manually install it to avoid running its this error by installing it yourself

`git clone https://github.com/libcpr/cpr.git`  
`cd cpr`   
`git checkout 1.11.0 `  
`mkdir build && cd build`  
`cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON ..`  
`make -j$(nproc) `   
`sudo make install  `  

### 3. Opencv: https://github.com/opencv/opencv

### 4. Eigen3: sudo apt install libeigen3-dev

### 5. depthai-core: https://github.com/luxonis/depthai-core/tree/v2_stable<br>
This is the v2 build not v3 as v3 does not support ros humble yet  
I am not sure about what I'm about to say, but I know there are some other dependencies and usb rules needed for depthai, which can be installed using<br>`sudo wget -qO- https://raw.githubusercontent.com/luxonis/depthai-ros/main/install_dependencies.sh | sudo bash` (yes it takes a long time)

## BUT NOTE
this installs I THINK depthai V3 which we cannot use with ROS humble, im not sure about it installing V3 directly but I'm sure about some libraries missing when using the depthai-core installed by this command, so after using it, we delete all the installed depthai libraries using  
`sudo rm -rf /opt/ros/humble/include/depthai*`   
`sudo rm -rf /opt/ros/humble/lib/libdepthai* `   
`sudo rm -rf /opt/ros/humble/share/depthai* `   

Now install depthai-core using  

`git clone -b v2_stable https://github.com/luxonis/depthai-core`    

then run  
`mkdir build && cd build`  
`cmake .. -DCMAKE_BUILD_TYPE=Release   `  
`sudo make install`  
`sudo ldconfig  `

### 6. depthai-ros: https://github.com/luxonis/depthai-ros/tree/humble

DO NOT FOLLOW THE RULES ON THE DOCS WEBSITE, IT LEADS TO A GREAT DEAL OF PAIN AND ANGER  
First we need some dependencies, run:

`sudo apt install -y ros-humble-camera-info-manager ros-humble-rclcpp ros-humble-rosidl-default-generators python3-colcon-common-extensions`

afterwards install rosdep:

`sudo apt install python3-rosdep  `   
`sudo rosdep init`  
`rosdep update  `  

Afterwards install the drivers:   

`mkdir -p dai_ws/src`  
`cd dai_ws/src`  
`git clone --branch <ros-distro> https://github.com/luxonis/depthai-ros.git `   
`cd ..`  
`rosdep install --from-paths src --ignore-src -r -y`  
`source /opt/ros/humble/setup.bash`  

Now, replace the depthai_examples cmakeslist with the one provided, this one correctly links the required libraries and ignores some problematic examples that we don't need and were causing brain tickling issues during building

if during building there were issues with `depthai_ros_msgs/srv/*.hpp no such file or directory`, head to `~/ros2_ws/install/depthai_ros_msgs/include/depthai_ros_msgs`and you will find another nested depthai_ros_msgs folder inside of it, COPY the content outstide of the nested folder

Now run `colcon build --symlink-install`

### 7. ORB_SLAM3
NOTE: before installing orb_slam3, please replace its cmakelist.txt with the given one<br>
https://docs.luxonis.com/software/ros/depthai-ros/build/

# Required ROS node
Install and run colcon-build for the orbslam3_node using<br>

`colcon build --packages-select orbslam3_node`

## Steps to run the SLAM:
We feed the camera output to orb slam3 using ros topics
**First**, initialize the camera ros nodes using

`ros2 launch depthai_examples stereo.launch.py`

This command should work if depthai_core and depthai_python were installed correctly

**Second** we need to feed the output as an input to orb slam3
we will use the ROS node previously installed for this task using <br>

`ros2 run orbslam3_node orbslam3_ros2`

Theoretically that's what it takes, unfortunately many errors may happen along the way due to each external library updating itself
with no humane regard to others, causing a great deal of pain<br>
I hope this doesn't happen though
