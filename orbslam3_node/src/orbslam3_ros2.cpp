#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <cv_bridge/cv_bridge.h>
#include <opencv2/opencv.hpp>
#include "include/System.h"
#include <opencv2/core.hpp>
#include <opencv2/core/persistence.hpp>
#include <iostream>

class ORBSLAM3Node : public rclcpp::Node {
public:
    ORBSLAM3Node()
    : Node("orbslam3_ros2_node")
    {
            std::string vocabFile = "/home/ggsya/ros2_ws/src/orbslam3_node/ORBvoc.txt";
            std::string yamlFile  = "/home/ggsya/ros2_ws/src/orbslam3_node/stereo.yaml";

        try {
        // Check if files can be opened
        std::ifstream f1(vocabFile);
        if (!f1.is_open()) throw std::runtime_error("Cannot open vocabulary file: " + vocabFile);

        std::ifstream f2(yamlFile);
        if (!f2.is_open()) throw std::runtime_error("Cannot open YAML file: " + yamlFile);

        std::cout << "Both files exist and are readable!" << std::endl;
            // Now create ORB-SLAM3 system
        // Now create ORB-SLAM3 system as a member pointer
            slam_ = std::make_unique<ORB_SLAM3::System>(
                vocabFile, yamlFile, ORB_SLAM3::System::STEREO, true
            );
        std::cout << "ORB-SLAM3 initialized successfully!" << std::endl;

        sub_left_ = create_subscription<sensor_msgs::msg::Image>(
            "/left/image_rect", 10,
            std::bind(&ORBSLAM3Node::leftCb, this, std::placeholders::_1));

        sub_right_ = create_subscription<sensor_msgs::msg::Image>(
            "/right/image_rect", 10,
            std::bind(&ORBSLAM3Node::rightCb, this, std::placeholders::_1));
            } 
            catch (const std::exception &e) {
                std::cerr << "Error: " << e.what() << std::endl;
                exit(69);
            }
    }

    ~ORBSLAM3Node() {
        slam_->Shutdown();
    }

private:
    void leftCb(const sensor_msgs::msg::Image::SharedPtr msg){
        left_ = cv_bridge::toCvShare(msg, "bgr8")->image.clone();
        track();
    }

    void rightCb(const sensor_msgs::msg::Image::SharedPtr msg){
        right_ = cv_bridge::toCvShare(msg, "bgr8")->image.clone();
        track();
    }

    void track(){
        if(left_.empty() || right_.empty()) return;

        double timestamp = std::chrono::duration<double>(
            std::chrono::steady_clock::now().time_since_epoch()
        ).count();

        slam_->TrackStereo(left_, right_, timestamp);

        cv::imshow("Left", left_);
        cv::imshow("Right", right_);
        cv::waitKey(1);
    }

    cv::Mat left_, right_;
    std::shared_ptr<ORB_SLAM3::System> slam_;

    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_left_;
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_right_;
};

int main(int argc, char** argv){



    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<ORBSLAM3Node>());
    rclcpp::shutdown();
    return 0;
}
