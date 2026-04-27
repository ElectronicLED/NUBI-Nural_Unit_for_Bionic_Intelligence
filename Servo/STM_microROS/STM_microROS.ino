#include <micro_ros_arduino.h>

#include "Herkulex.h"

#include <stdio.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>

#include <std_msgs/msg/int16.h>
#include <std_msgs/msg/int16_multi_array.h>
#include <std_msgs/msg/bool.h>
#include <std_msgs/msg/u_int8_multi_array.h>
//#include <std_msgs/msg/string.h>

#include <Servo.h>

#include <string.h>

#define NUM_SERVOS 2

Servo gripper[NUM_SERVOS];

// ------------------- micro-ROS objects defined once -------------------
rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;

// ------------------- micro-ROS Subscribers object -------------------
rcl_subscription_t leg_command_subscriber;
rcl_subscription_t upperbody_command_subscriber;
rcl_subscription_t torque_command_subscriber;
rcl_subscription_t gripper_command_subscriber;
rcl_subscription_t color_cmd_subscriber;

// ------------------- micro-ROS Publishers object -------------------
rcl_publisher_t leg_pos_feedback_publisher;
rcl_publisher_t upperbody_pos_feedback_publisher;
rcl_publisher_t status_publisher;
rcl_publisher_t color_feedback_publisher;
rcl_publisher_t torque_feedback_publisher;

// ------------------- micro-ROS Service object -------------------


// ------------------- micro-ROS Timer objects -------------------

rcl_timer_t color_timer;
rcl_timer_t torque_timer;

//Subscriber messages
//std_msgs__msg__Int16 msg;
std_msgs__msg__Int16MultiArray legs_command;
std_msgs__msg__Int16MultiArray upperbody_command;
std_msgs__msg__Bool torque_command;
std_msgs__msg__Int16MultiArray gripper_command;
std_msgs__msg__Int16MultiArray color_command;

//Publisher messages
std_msgs__msg__Int16MultiArray legs_feedback;
std_msgs__msg__Int16MultiArray upperbody_feedback;
std_msgs__msg__Int16MultiArray status_msg;
std_msgs__msg__Int16MultiArray color_feedback;
std_msgs__msg__UInt8MultiArray torque_feedback;

#define left_gripper_pin PB9
#define right_gripper_pin PB13

// loops on servos by turn
int feedback_index = 0;
// number of motors
int n=20;

bool torque_state = true;

const uint leg_motor_indecies[12] = {16,6,7,8,10,9,17,11,12,13,15,14};
const uint upper_motor_indecies[7] = {0,1,2,3,4,5,19};
byte statusError, statusDetail;

float timer_frequency = 3;
unsigned long timer_period_ms = (unsigned long) (1000/timer_frequency);
unsigned long torque_lastTime = 0;
unsigned long color_lastTime = 0;
unsigned long torque_currentTime = 0;
unsigned long color_currentTime = 0;

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

// --------------------- Subsribers Callback Functions ---------------------
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
  torque_currentTime = millis();
  if (torque_currentTime - torque_lastTime < timer_period_ms) return;
  torque_lastTime = torque_currentTime;


  const std_msgs__msg__Bool * msg = (const std_msgs__msg__Bool *)msgin;

  if(msg->data == true){
    for(int i = 0; i<n;i++){
  //    Herkulex.moveOneAngle(leg_motor_indecies[i], msg->data.data[i], 1000, LED_BLUE);
      Herkulex.torqueON(i);
    }
    torque_state = true;
  }
  else{
    for(int i = 0; i<n;i++){
  //    Herkulex.moveOneAngle(leg_motor_indecies[i], msg->data.data[i], 1000, LED_BLUE);
      Herkulex.torqueOFF(i);
    }
    torque_state = false;
  }
}

void gripper_callback(const void* msgin) {
  const std_msgs__msg__Int16MultiArray* msg = 
  (const std_msgs__msg__Int16MultiArray*)msgin;
  for (int i = 0; i < NUM_SERVOS; i++) {

    gripper[i].write(msg->data.data[i]);
    
  }
}

void color_cmd_callback(const void* msgin) {

  color_currentTime = millis();
  if (color_currentTime - color_lastTime < timer_period_ms) return;
  color_lastTime = color_currentTime;


  const std_msgs__msg__Int16MultiArray* msg =
      (const std_msgs__msg__Int16MultiArray*)msgin;

  int16_t led_id    = msg->data.data[0];
  int16_t led_color = msg->data.data[1];

  Herkulex.setLed(led_id, led_color);
}

// --------------------- Subsribers Setup Functions ---------------------
void leg_cmd_sub_setup(){
  static int16_t memory_buffer[12]; 
  legs_command.data.capacity = 12;
  legs_command.data.data = memory_buffer;
  legs_command.data.size = 0;

  RCCHECK(rclc_subscription_init_default(
    &leg_command_subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "legs_command"));
  
  RCCHECK(rclc_executor_add_subscription(&executor, &leg_command_subscriber, &legs_command, &legs_cmd_callback, ON_NEW_DATA));
}

void upperbody_cmd_sub_setup(){
  static int16_t memory_buffer1[7]; 
  upperbody_command.data.capacity = 7;
  upperbody_command.data.data = memory_buffer1;
  upperbody_command.data.size = 0;

  RCCHECK(rclc_subscription_init_default(
    &upperbody_command_subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "upperbody_command"));
  
  RCCHECK(rclc_executor_add_subscription(&executor, &upperbody_command_subscriber, &upperbody_command, &upperbody_cmd_callback, ON_NEW_DATA));
}

void torque_cmd_sub_setup(){
  RCCHECK(rclc_subscription_init_default(
    &torque_command_subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Bool),
    "torque_command"));

  RCCHECK(rclc_executor_add_subscription(&executor, &torque_command_subscriber, &torque_command, &torque_cmd_callback, ON_NEW_DATA));
}

void gripper_sub_setup() {
  // Allocate memory for incoming Float64MultiArray
  static int16_t memory_buffer2[2]; 
  gripper_command.data.capacity = 2;
  gripper_command.data.size = 0;
  gripper_command.data.data = memory_buffer2;

  rclc_subscription_init_default(
    &gripper_command_subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "gripper_command");

  rclc_executor_add_subscription(
    &executor,
    &gripper_command_subscriber,
    &gripper_command,
    &gripper_callback,
    ON_NEW_DATA);

}

void color_sub_setup(){
  static int16_t memory_buffer3[2]; 
  color_command.data.capacity = 2;
  color_command.data.size = 2;
  color_command.data.data = memory_buffer3;

  rclc_subscription_init_default(
    &color_cmd_subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "LED_color_cmd");

  rclc_executor_add_subscription(
    &executor, 
    &color_cmd_subscriber, 
    &color_command,
    &color_cmd_callback, 
    ON_NEW_DATA);
}

// --------------------- Timers Setup Functions ---------------------
void color_timer_setup(){
  static int16_t feedback_buffer3[20];
  // Link the buffer to the message struct
  color_feedback.data.capacity = 20;
  color_feedback.data.data = feedback_buffer3;
  color_feedback.data.size = 20;

  rclc_publisher_init_default(
    &color_feedback_publisher,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "LED_color_feedback");

  rclc_timer_init_default(
    &color_timer,
    &support,
    RCL_MS_TO_NS(timer_period_ms),      // period in nanoseconds
    color_timer_callback);
  
  rclc_executor_add_timer(&executor, &color_timer);
}

void torque_timer_setup(){
  static u_int8_t feedback_buffer4[20];
  // Link the buffer to the message struct
  torque_feedback.data.capacity = 20;
  torque_feedback.data.data = feedback_buffer4;
  torque_feedback.data.size = 20;

  rclc_publisher_init_default(
    &torque_feedback_publisher,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, UInt8MultiArray),
    "torque_feedback");

  rclc_timer_init_default(
    &torque_timer,
    &support,
    RCL_MS_TO_NS(timer_period_ms),      // period in nanoseconds
    torque_timer_callback);
  
  rclc_executor_add_timer(&executor, &torque_timer);
}

// --------------------- Timers Callback Functions ---------------------
void color_timer_callback(rcl_timer_t * timer, int64_t last_call_time)
{
  (void) last_call_time;

  if (timer != NULL) {
    for(int i = 0; i<20; i++){
      color_feedback.data.data[i] = (int16_t)Herkulex.getLed(i);
    }

    rcl_publish(&color_feedback_publisher, &color_feedback, NULL);
  }
}

void torque_timer_callback(rcl_timer_t * timer, int64_t last_call_time)
{
  (void) last_call_time;

  if (timer != NULL) {
    for(int i = 0; i<20; i++){
      if(Herkulex.getTorque(i) == 0x60){
        torque_feedback.data.data[i] = 1;
      }
      else if(Herkulex.getTorque(i) == 0x00){
        torque_feedback.data.data[i] = 0;
      }
    }

    rcl_publish(&torque_feedback_publisher, &torque_feedback, NULL);
  }
}

void setup() {
  pinMode(LED_BUILTIN,OUTPUT);

  gripper[0].attach(right_gripper_pin);
  gripper[1].attach(left_gripper_pin);

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

  static int16_t feedback_buffer2[40];
  // Link the buffer to the message struct
  status_msg.data.capacity = 40;
  status_msg.data.data = feedback_buffer2;
  status_msg.data.size = 40;

  

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

  rclc_publisher_init_default(
    &status_publisher,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "motor_status");

  // create executor
  // make sure you change the number to the number of subscribers
  RCCHECK(rclc_executor_init(&executor, &support.context, 7, &allocator));  
  //RCCHECK(rclc_executor_add_subscription(&executor, &subscriber, &msg, &subscription_callback, ON_NEW_DATA));
  leg_cmd_sub_setup();        //1
  upperbody_cmd_sub_setup();  //2
  torque_cmd_sub_setup();     //3
  gripper_sub_setup();        //4
  color_sub_setup();          //5
  color_timer_setup();        //6
  torque_timer_setup();       //7

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
  //digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));

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

  //Status Publisher
  for(int i=0; i<20; i++){
    byte result = Herkulex.stat(i, statusError, statusDetail);

    if (result == (byte)-1 || result == (byte)-2) {

    }
    else{
      status_msg.data.data[i * 2]     = statusError;
      status_msg.data.data[i * 2 + 1] = statusDetail;
    }
  }

  // 2. Publish the message
  // We pass NULL as the 3rd argument (allocation) because it's rarely used
  RCSOFTCHECK(rcl_publish(&leg_pos_feedback_publisher, &legs_feedback, NULL));
  RCSOFTCHECK(rcl_publish(&upperbody_pos_feedback_publisher, &upperbody_feedback, NULL));
  rcl_publish(&status_publisher, &status_msg, NULL);


  RCCHECK(rclc_executor_spin_some(&executor, RCL_MS_TO_NS(2)));
}
