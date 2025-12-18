#include <micro_ros_arduino.h>

#include <Herkulex.h>

#include <stdio.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>

#include <std_msgs/msg/int16.h>
#include <std_msgs/msg/int16_multi_array.h>
#include <std_msgs/msg/bool.h>

rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;
rcl_timer_t timer;
rcl_subscription_t leg_command_subscriber;
rcl_subscription_t upperbody_command_subscriber;
rcl_subscription_t torque_command_subscriber;
rcl_publisher_t leg_pos_feedback_publisher;
rcl_publisher_t upperbody_pos_feedback_publisher;


//std_msgs__msg__Int16 msg;
std_msgs__msg__Int16MultiArray legs_command;
std_msgs__msg__Int16MultiArray legs_feedback;

std_msgs__msg__Int16MultiArray upperbody_command;
std_msgs__msg__Int16MultiArray upperbody_feedback;

std_msgs__msg__Bool torque_command;

// loops on servos by turn
int feedback_index = 0;
// number of motors
int n=19;

const uint leg_motor_indecies[12] = {16,6,7,8,10,9,17,11,12,13,15,14};
const uint upper_motor_indecies[7] = {0,1,2,3,4,5,19};


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

void upperbody_cmd_callback(const void * msgin){

  for(int i = 0; i<7;i++){
    // Directly accessing the global struct
    Herkulex.moveOneAngle(upper_motor_indecies[i], upperbody_command.data.data[i], 1000, LED_BLUE);
  }
}

void torque_cmd_callback(const void * msgin){
  //The incoming message is received as a generic void pointer.
  //the following line casts the void pointer to the specific message type 
  //so you can access the data.
  const std_msgs__msg__Bool * msg = (const std_msgs__msg__Bool *)msgin;

  if(msg->data == true){
    for(int i = 0; i<n;i++){
  //    Herkulex.moveOneAngle(leg_motor_indecies[i], msg->data.data[i], 1000, LED_BLUE);
      Herkulex.torqueON(i);
    }
  }
  else{
    for(int i = 0; i<n;i++){
  //    Herkulex.moveOneAngle(leg_motor_indecies[i], msg->data.data[i], 1000, LED_BLUE);
      Herkulex.torqueOFF(i);
    }
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

  static int16_t memory_buffer1[7]; 
  upperbody_command.data.capacity = 7;
  upperbody_command.data.data = memory_buffer1;
  upperbody_command.data.size = 0;

  // Create a static buffer to hold the data you want to send
  static int16_t feedback_buffer[12]; 
  // Link the buffer to the message struct
  legs_feedback.data.capacity = 12;
  legs_feedback.data.data = feedback_buffer;
  legs_feedback.data.size = 12; // IMPORTANT: Tell ROS how many items you are sending

  static int16_t feedback_buffer1[7]; 
  // Link the buffer to the message struct
  upperbody_feedback.data.capacity = 7;
  upperbody_feedback.data.data = feedback_buffer1;
  upperbody_feedback.data.size = 7; 

  // create subscriber
  RCCHECK(rclc_subscription_init_default(
    &leg_command_subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "legs_command"));

  RCCHECK(rclc_subscription_init_default(
    &upperbody_command_subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "upperbody_command"));

  RCCHECK(rclc_subscription_init_default(
    &torque_command_subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Bool),
    "torque_command"));

  // create publisher
  RCCHECK(rclc_publisher_init_default(
    &leg_pos_feedback_publisher,
    &node,
    // ROSIDL_GET_MSG_TYPE_SUPPORT(package_name, subfolder, message_name)
    // fetches the "Instruction Manual" for a specific message_name in package_name/subfolder_name.
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "legs_feedback"));

  RCCHECK(rclc_publisher_init_default(
    &upperbody_pos_feedback_publisher,
    &node,
    // ROSIDL_GET_MSG_TYPE_SUPPORT(package_name, subfolder, message_name)
    // fetches the "Instruction Manual" for a specific message_name in package_name/subfolder_name.
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "upperbody_feedback"));

  // create executor
  // make sure you change the number to the number of subscribers
  RCCHECK(rclc_executor_init(&executor, &support.context, 3, &allocator));  
  //RCCHECK(rclc_executor_add_subscription(&executor, &subscriber, &msg, &subscription_callback, ON_NEW_DATA));
  RCCHECK(rclc_executor_add_subscription(&executor, &leg_command_subscriber, &legs_command, &legs_cmd_callback, ON_NEW_DATA));
  RCCHECK(rclc_executor_add_subscription(&executor, &upperbody_command_subscriber, &upperbody_command, &upperbody_cmd_callback, ON_NEW_DATA));
  RCCHECK(rclc_executor_add_subscription(&executor, &torque_command_subscriber, &torque_command, &torque_cmd_callback, ON_NEW_DATA));

  //Servo initialization
  delay(2000);  //a delay to have time for serial monitor opening
  Herkulex.begin(115200,PA9,PA10); //open serial 
  for(int i=0; i<n; i++){
    Herkulex.reboot(i); //reboot motors
    delay(20);
  }
  delay(500); 
  Herkulex.initialize(); //initialize motors
  delay(200);  
}




void loop() {
  // put your main code here, to run repeatedly:
  digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));

  legs_feedback.data.data[feedback_index] = Herkulex.getAngle(leg_motor_indecies[feedback_index]);

  // 2. Increment index for the next loop (Wrap around at 12)
  feedback_index++;
  if (feedback_index >= 12) {
    feedback_index = 0;
  }

  // for(int i = 0; i < 12; i++) { 
  //   legs_feedback.data.data[i] = Herkulex.getAngle(leg_motor_indecies[i]);
  // }

  for(int i = 0; i < 7; i++) { 
    upperbody_feedback.data.data[i] = Herkulex.getAngle(upper_motor_indecies[i]);
  }

  // 2. Publish the message
  // We pass NULL as the 3rd argument (allocation) because it's rarely used
  RCSOFTCHECK(rcl_publish(&leg_pos_feedback_publisher, &legs_feedback, NULL));
  RCSOFTCHECK(rcl_publish(&upperbody_pos_feedback_publisher, &upperbody_feedback, NULL));


  RCCHECK(rclc_executor_spin_some(&executor, RCL_MS_TO_NS(2)));
}
