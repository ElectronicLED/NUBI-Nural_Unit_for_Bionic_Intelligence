#include <micro_ros_arduino.h>

#include <Herkulex.h>

#include <stdio.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>

#include <std_msgs/msg/int16.h>
#include <std_msgs/msg/int16_multi_array.h>

rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;
rcl_timer_t timer;
rcl_subscription_t leg_command_subscriber;
rcl_publisher_t leg_pos_feedback_publisher;


//std_msgs__msg__Int16 msg;
std_msgs__msg__Int16MultiArray legs_command;
std_msgs__msg__Int16MultiArray legs_feedback;




int n=18;

const uint leg_motor_indecies[12] = {16,6,7,8,10,9,17,11,12,13,15,14};


// macros to check if any function returns anything other than RCL_RET_OK othwerwise stick to error or pass
#define RCCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){error_loop();}}
// same check but without sticking in error loop
#define RCSOFTCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){}}

void error_loop(){
  while(1){
    digitalWrite(PB6, !digitalRead(PB6));
    delay(100);
  }
}

void legs_cmd_callback(const void * msgin){
  //The incoming message is received as a generic void pointer.
  //the following line casts the void pointer to the specific message type 
  //so you can access the data.
  // const std_msgs__msg__Int16MultiArray * msg = (const std_msgs__msg__Int16MultiArray *)msgin;
  // for(int i = 0; i<12;i++){
  //   Herkulex.moveOneAngle(leg_motor_indecies[i], msg->data.data[i], 1000, LED_BLUE);
  // }
  for(int i = 0; i<12;i++){
    // Directly accessing the global struct
    Herkulex.moveOneAngle(leg_motor_indecies[i], legs_command.data.data[i], 1000, LED_BLUE);
  }
}


void setup() {
  pinMode(LED_BUILTIN,OUTPUT);

  // Sets up the serial communication (usually USB-Serial or UART) to 
  // talk to the micro-ROS Agent on your PC
  set_microros_transports();
  // put your pinMode definitions here

  delay(2000);

  // get default memory allocator
  allocator = rcl_get_default_allocator();

  //create init_options
  RCCHECK(rclc_support_init(&support, 0, NULL, &allocator));
  // create node
  RCCHECK(rclc_node_init_default(&node, "NUBI_STM_NODE", "", &support));

  // Int16MultiArray does not automatically create space to hold the incoming array data.
  // We need space for 12 integers
  static int16_t memory_buffer[12]; 
  legs_command.data.capacity = 12;
  legs_command.data.data = memory_buffer;
  legs_command.data.size = 0;

  // Create a static buffer to hold the data you want to send
  static int16_t feedback_buffer[12]; 
  // Link the buffer to the message struct
  legs_feedback.data.capacity = 12;
  legs_feedback.data.data = feedback_buffer;
  legs_feedback.data.size = 12; // IMPORTANT: Tell ROS how many items you are sending

  // create subscriber
  RCCHECK(rclc_subscription_init_default(
    &leg_command_subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "legs_command"));

  // create publisher
  RCCHECK(rclc_publisher_init_default(
    &leg_pos_feedback_publisher,
    &node,
    // ROSIDL_GET_MSG_TYPE_SUPPORT(package_name, subfolder, message_name)
    // fetches the "Instruction Manual" for a specific message_name in package_name/subfolder_name.
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "legs_feedback"));

  // create executor
  RCCHECK(rclc_executor_init(&executor, &support.context, 1, &allocator));  
  //RCCHECK(rclc_executor_add_subscription(&executor, &subscriber, &msg, &subscription_callback, ON_NEW_DATA));
  RCCHECK(rclc_executor_add_subscription(&executor, &leg_command_subscriber, &legs_command, &legs_cmd_callback, ON_NEW_DATA));

  //Servo initialization
  delay(2000);  //a delay to have time for serial monitor opening
  Herkulex.begin(115200,PA9,PA10); //open serial 
  for(int i=1; i<=n; i++){
    Herkulex.reboot(i); //reboot first motor
    delay(20);
  }
  delay(500); 
  Herkulex.initialize(); //initialize motors
  delay(200);  
}

void loop() {
  // put your main code here, to run repeatedly:

  for(int i = 0; i < 12; i++) { 
    legs_feedback.data.data[i] = Herkulex.getPosition(leg_motor_indecies[i]);
  }

  // 2. Publish the message
  // We pass NULL as the 3rd argument (allocation) because it's rarely used
  RCSOFTCHECK(rcl_publish(&leg_pos_feedback_publisher, &legs_feedback, NULL));


  RCCHECK(rclc_executor_spin_some(&executor, RCL_MS_TO_NS(100)));
}
