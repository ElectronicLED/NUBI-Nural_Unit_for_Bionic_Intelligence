cmake_minimum_required(VERSION 3.5)
project(orbslam3_node)

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(OpenCV REQUIRED)
find_package(Pangolin REQUIRED)

include_directories(
    ${OpenCV_INCLUDE_DIRS}
    $ENV{HOME}/Dev/Pangolin/build
    $ENV{HOME}/Dev/ORB_SLAM3
    /usr/include/eigen3
    $ENV{HOME}/Dev/ORB_SLAM3/include/CameraModels
    $ENV{HOME}/Dev/ORB_SLAM3/include
)

link_directories(
    $ENV{HOME}/Dev/ORB_SLAM3/lib
)

add_executable(orbslam3_ros2 src/orbslam3_ros2.cpp)
ament_target_dependencies(orbslam3_ros2 rclcpp sensor_msgs cv_bridge OpenCV)

target_link_libraries(orbslam3_ros2
    ORB_SLAM3
    pango_core
    pango_opengl
    pango_glgeometry
    pango_windowing
    pango_display
    
)

install(TARGETS orbslam3_ros2
  DESTINATION lib/${PROJECT_NAME})

ament_package()
