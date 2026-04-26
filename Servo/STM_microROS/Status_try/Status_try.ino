#include <micro_ros_arduino.h>

#include "Herkulex.h"

#include <stdio.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>

#include <std_msgs/msg/int16_multi_array.h>

// ------------------- micro-ROS objects defined once -------------------
rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;
rcl_timer_t timer;

// ------------------- micro-ROS Publishers object -------------------
rcl_publisher_t status_publisher;

std_msgs__msg__Int16MultiArray status_msg;

//int n = 0;
static int16_t feedback_buffer[40]; 
byte statusError, statusDetail;

void microros_setup(){ 
  set_microros_transports(); 
  delay(2000); 
  allocator = rcl_get_default_allocator(); 
  rclc_support_init(&support, 0, NULL, &allocator); 
  rclc_node_init_default(&node, "TEST_STM_NODE", "", &support); 
  }

void setup() {
  // put your setup code here, to run once:
  microros_setup(); 
  delay(2000); //a delay to have time for serial monitor opening 
  
  Herkulex.begin(115200,PA9,PA10); //open serial 
  for(int i=0; i<19;i++){
   Herkulex.reboot(i); //reboot motors  
  }
  delay(500); 
  Herkulex.initialize(); //initialize motors 
  delay(200); 

  // Initialize publisher
  rclc_publisher_init_default(
    &status_publisher,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "motor_status");
  status_msg.data.capacity = 40;
  status_msg.data.data = feedback_buffer;
  status_msg.data.size = 40;

}

void loop() {
  // put your main code here, to run repeatedly:
  for(int i=0; i<20; i++){
    byte result = Herkulex.stat(i, statusError, statusDetail);

    if (result == (byte)-1 || result == (byte)-2) {

    }
    else{
      status_msg.data.data[i * 2]     = statusError;
      status_msg.data.data[i * 2 + 1] = statusDetail;
    }
  }
  //status_msg.data = Herkulex.stat(n);
  rcl_publish(&status_publisher, &status_msg, NULL);
  rclc_executor_spin_some(&executor, RCL_MS_TO_NS(100));
  delay(5);

}



