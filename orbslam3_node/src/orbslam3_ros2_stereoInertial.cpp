#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include <sensor_msgs/msg/imu.hpp>
#include <cv_bridge/cv_bridge.h>
#include <opencv2/opencv.hpp>
#include "include/System.h"
#include <opencv2/core.hpp>
#include <opencv2/core/persistence.hpp>
#include <iostream>
#include <vector>
#include <mutex>
#include <deque>

class ORBSLAM3VI : public rclcpp::Node {
public:
    ORBSLAM3VI()
    : Node("orbslam3_ros2_vi_node"), 
      last_imu_t_(0.0),
      system_initialized_(false),
      last_processed_timestamp_(0.0)
    {
        std::string vocabFile = "/home/ggsya/ros2_ws/src/orbslam3_node/ORBvoc.txt";
        std::string yamlFile  = "/home/ggsya/ros2_ws/src/orbslam3_node/stereo-inertial.yaml";
        
        try {
            std::ifstream f1(vocabFile);
            if (!f1.is_open()) throw std::runtime_error("Cannot open vocabulary file: " + vocabFile);
            std::ifstream f2(yamlFile);
            if (!f2.is_open()) throw std::runtime_error("Cannot open YAML file: " + yamlFile);
            
            std::cout << "Files OK!" << std::endl;
            
            slam_ = std::make_unique<ORB_SLAM3::System>(
                vocabFile, yamlFile, ORB_SLAM3::System::IMU_STEREO, true
            );
            
            sub_left_ = create_subscription<sensor_msgs::msg::Image>(
                "/left/image_rect", 10,
                std::bind(&ORBSLAM3VI::leftCb, this, std::placeholders::_1));
            
            sub_right_ = create_subscription<sensor_msgs::msg::Image>(
                "/right/image_rect", 10,
                std::bind(&ORBSLAM3VI::rightCb, this, std::placeholders::_1));
            
            sub_imu_ = create_subscription<sensor_msgs::msg::Imu>(
                "/imu", 200,
                std::bind(&ORBSLAM3VI::imuCb, this, std::placeholders::_1));
        } 
        catch (const std::exception &e) {
            std::cerr << "Error: " << e.what() << std::endl;
            exit(69);
        }
    }
    
    ~ORBSLAM3VI() {
        slam_->Shutdown();
    }

private:
    void leftCb(const sensor_msgs::msg::Image::SharedPtr msg){
        std::lock_guard<std::mutex> lock(mutex_);
        left_ = cv_bridge::toCvShare(msg, "mono8")->image.clone();
        left_timestamp_ = msg->header.stamp.sec + msg->header.stamp.nanosec * 1e-9;
        left_received_ = true;
        tryTrack();
    }
    
    void rightCb(const sensor_msgs::msg::Image::SharedPtr msg){
        std::lock_guard<std::mutex> lock(mutex_);
        right_ = cv_bridge::toCvShare(msg, "mono8")->image.clone();
        right_timestamp_ = msg->header.stamp.sec + msg->header.stamp.nanosec * 1e-9;
        right_received_ = true;
        tryTrack();
    }
    
    void tryTrack(){
        // Only track when we have BOTH new images
        if (!left_received_ || !right_received_) return;
        
        // Reset flags
        left_received_ = false;
        right_received_ = false;
        
        track();
    }
    
    void imuCb(const sensor_msgs::msg::Imu::SharedPtr msg){
        std::lock_guard<std::mutex> lock(mutex_);
        
        double t = msg->header.stamp.sec + msg->header.stamp.nanosec * 1e-9;
        
        // Validate IMU data - check for NaN or infinite values
        if (!std::isfinite(msg->linear_acceleration.x) || 
            !std::isfinite(msg->linear_acceleration.y) ||
            !std::isfinite(msg->linear_acceleration.z) ||
            !std::isfinite(msg->angular_velocity.x) ||
            !std::isfinite(msg->angular_velocity.y) ||
            !std::isfinite(msg->angular_velocity.z)) {
            RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 5000,
                                 "Invalid IMU data detected! Skipping.");
            return;
        }
        
        // Check for monotonic timestamps
        if (t <= last_imu_t_) {
            RCLCPP_WARN_THROTTLE(this->get_logger(), *this->get_clock(), 5000,
                        "Non-monotonic IMU timestamp! t=%.6f, last=%.6f", t, last_imu_t_);
            return;
        }
        last_imu_t_ = t;
        
        cv::Point3f acc(msg->linear_acceleration.x,
                        msg->linear_acceleration.y,
                        msg->linear_acceleration.z);
        
        cv::Point3f gyro(msg->angular_velocity.x,
                         msg->angular_velocity.y,
                         msg->angular_velocity.z);
        
        imu_buffer_.push_back(ORB_SLAM3::IMU::Point(acc, gyro, t));
        
        // Keep buffer manageable (store last 5 seconds of IMU data)
        while (!imu_buffer_.empty() && 
               (t - imu_buffer_.front().t) > 5.0) {
            imu_buffer_.pop_front();
        }
        
        // Mark system as initialized after receiving enough IMU data
        if (!system_initialized_ && imu_buffer_.size() > 50) {
            system_initialized_ = true;
            RCLCPP_INFO(this->get_logger(), "✓ IMU buffer initialized with %lu measurements", 
                        imu_buffer_.size());
        }
    }
    
    void track(){
        if(left_.empty() || right_.empty()) return;
        
        double stereo_diff = std::abs(left_timestamp_ - right_timestamp_);
        if(stereo_diff > 0.01) {
            RCLCPP_WARN(this->get_logger(), 
                        "⚠ Stereo desync: %.1fms - skipping frame", stereo_diff * 1000.0);
            return;
        }
        
        // Wait for IMU initialization
        if (!system_initialized_) {
            RCLCPP_INFO_THROTTLE(this->get_logger(), *this->get_clock(), 2000,
                                 "Waiting for IMU initialization... (%lu measurements)", 
                                 imu_buffer_.size());
            return;
        }
        
        double timestamp = left_timestamp_;
        
        // Get IMU measurements between last processed frame and current frame
        std::vector<ORB_SLAM3::IMU::Point> vImuMeas;
        
        // For the very first frame, include some IMU history
        double start_time = (last_processed_timestamp_ == 0.0) ? 
                            (timestamp - 0.5) : last_processed_timestamp_;
        
        // Collect IMU measurements in the time window
        for(const auto& imu : imu_buffer_){
            if(imu.t > start_time && imu.t <= timestamp){
                vImuMeas.push_back(imu);
            }
        }
        
        // Remove old IMU data (keep 2 seconds of history for safety)
        while (!imu_buffer_.empty() && 
               imu_buffer_.front().t < timestamp - 2.0) {
            imu_buffer_.pop_front();
        }
        
        // Debug info
        double time_delta = timestamp - last_processed_timestamp_;
        double expected_delta = 1.0 / 28.0; // Expected at 28 fps
        double fps = (time_delta > 0) ? 1.0 / time_delta : 0.0;
        
        RCLCPP_INFO(this->get_logger(), 
                    "Track: t=%.3f, ΔT=%.0fms (%.1f fps), IMU=%lu, buf=%lu, sync=%.1fms", 
                    timestamp, time_delta * 1000.0, fps, vImuMeas.size(), 
                    imu_buffer_.size(), stereo_diff * 1000.0);
        
        // Warn if frame interval is unexpected
        if (last_processed_timestamp_ != 0.0 && 
            std::abs(time_delta - expected_delta) > 0.02) {
            RCLCPP_WARN(this->get_logger(), 
                        "⚠ Frame timing irregular! Expected ~%.0fms, got %.0fms",
                        expected_delta * 1000.0, time_delta * 1000.0);
        }
        
        // Check if we have IMU measurements (skip check for first frame)
        if(vImuMeas.empty() && last_processed_timestamp_ != 0.0){
            RCLCPP_WARN(this->get_logger(), 
                        "⚠ No IMU measurements between %.3f and %.3f! Skipping frame.", 
                        last_processed_timestamp_, timestamp);
            return;
        }
        
        // Warn about low IMU rate
        if (last_processed_timestamp_ != 0.0 && time_delta > 0.001) {
            double imu_rate = vImuMeas.size() / time_delta;
            if (imu_rate < 50.0) {
                RCLCPP_WARN(this->get_logger(), 
                            "⚠ Low IMU rate: %.1f Hz (expected ~200 Hz)", imu_rate);
            }
        }
        
        last_processed_timestamp_ = timestamp;
        
        try {
            // THIS is where feature extraction happens!
            slam_->TrackStereo(left_, right_, timestamp, vImuMeas);
            
            // Let SLAM's viewer handle the visualization - don't interfere
            
        } catch (const std::exception& e) {
            RCLCPP_ERROR(this->get_logger(), "❌ SLAM tracking failed: %s", e.what());
        }
    }
    
    cv::Mat left_, right_;
    double left_timestamp_ = 0.0;
    double right_timestamp_ = 0.0;
    bool left_received_ = false;
    bool right_received_ = false;
    double last_processed_timestamp_;
    double last_imu_t_;
    bool system_initialized_;
    std::deque<ORB_SLAM3::IMU::Point> imu_buffer_;
    std::unique_ptr<ORB_SLAM3::System> slam_;
    std::mutex mutex_;
    
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_left_;
    rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_right_;
    rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr sub_imu_;
};

int main(int argc, char** argv){
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<ORBSLAM3VI>());
    rclcpp::shutdown();
    return 0;
}