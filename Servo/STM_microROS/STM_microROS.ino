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
#include <std_msgs/msg/string.h>
#include <Servo.h>
#include <string.h>
// rcutils logging is unreliable on STM32 microROS — use /nubi_debug publisher instead
#define NUM_SERVOS 2
// ------------------- Timer frequencies -------------------
// Torque reading is slow (~12ms/servo × 20 = 240ms) so keep it at 1 Hz
#define TORQUE_TIMER_HZ    1
#define STATUS_TIMER_HZ    2

const unsigned long torque_timer_period_ms = (unsigned long)(1000 / TORQUE_TIMER_HZ);  // 1000ms
const unsigned long status_timer_period_ms = (unsigned long)(1000 / STATUS_TIMER_HZ);  //  500ms
// number of motors
int n=20;


const uint leg_motor_indecies[12] = {16,6,7,8,10,9,17,11,12,13,15,14};
const uint upper_motor_indecies[7] = {0,1,2,3,4,18,19};
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
rcl_publisher_t debug_publisher;


// -------------------Timer objects -------------------
rcl_timer_t color_timer;
rcl_timer_t torque_timer;
rcl_timer_t status_timer;

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

// Debug string message — reused for all log publishes
std_msgs__msg__String debug_msg;
static char debug_char_buf[128];

// Helper: publish a debug string to /nubi_debug
void debug_log(const char* msg) {
  debug_msg.data.data = debug_char_buf;
  debug_msg.data.capacity = sizeof(debug_char_buf);
  strncpy(debug_char_buf, msg, sizeof(debug_char_buf) - 1);
  debug_char_buf[sizeof(debug_char_buf) - 1] = '\0';
  debug_msg.data.size = strlen(debug_char_buf);
  rcl_publish(&debug_publisher, &debug_msg, NULL);
}

#define left_gripper_pin PB9
#define right_gripper_pin PB13

// loops on servos by turn — separate indices for legs and upper body
int leg_feedback_index = 0;
int upper_feedback_index = 0;
#define FEEDBACK_TOTAL 19   // 12 legs + 7 upper (kept for reference)


byte statusError, statusDetail;


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
  // Queue all 12 leg servos then fire simultaneously with actionAll
  for(int i = 0; i<12;i++){
    Herkulex.moveAllAngle(leg_motor_indecies[i], legs_command.data.data[i], LED_BLUE);
  }
  Herkulex.actionAll(500);  // 500ms execution time — reduce if hardware allows
}

void upperbody_cmd_callback(const void * msgin){
  // Queue all 7 servos then fire simultaneously with actionAll
  // actionAll(ms): ms = time for servos to reach position; lower = faster
  for(int i = 0; i<7;i++){
    Herkulex.moveAllAngle(upper_motor_indecies[i], upperbody_command.data.data[i], LED_BLUE);
  }
  Herkulex.actionAll(500);  // 500ms execution time — reduce further if hardware allows
}

void torque_cmd_callback(const void * msgin){
  //The incoming message is received as a generic void pointer.
  //the following line casts the void pointer to the specific message type 
  //so you can access the data.
  const std_msgs__msg__Bool * msg = (const std_msgs__msg__Bool *)msgin;

  if(msg->data == true){
    Herkulex.torqueON(BROADCAST_ID);   // single broadcast packet to all servos
  }
  else{
    Herkulex.torqueOFF(BROADCAST_ID);  // single broadcast packet to all servos
  }
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



// --------------------- Timers Setup Functions ---------------------

void torque_timer_callback(rcl_timer_t * timer, int64_t last_call_time)
{
  (void) last_call_time;

  if (timer != NULL) {
    unsigned long t0_torque = micros();
    for(int i = 0; i<20; i++){
      byte tq = Herkulex.getTorque(i);
      if(tq == 0x60){
        torque_feedback.data.data[i] = 1;
      }
      else if(tq == 0x00){
        torque_feedback.data.data[i] = 0;
      }
    }
    unsigned long elapsed_torque = micros() - t0_torque;
    char log_buf[128];
    snprintf(log_buf, sizeof(log_buf), "[NUBI] torque read 20 servos: %lu us", elapsed_torque);
    debug_log(log_buf);

    rcl_publish(&torque_feedback_publisher, &torque_feedback, NULL);
  }
}



void status_timer_callback(rcl_timer_t * timer, int64_t last_call_time)
{
  (void) last_call_time;
  if (timer != NULL) {
    unsigned long t0_status = micros();
    for(int i = 0; i < 20; i++){
      byte result = Herkulex.stat(i, statusError, statusDetail);
      if (result != (byte)-1 && result != (byte)-2){
        status_msg.data.data[i * 2]     = statusError;
        status_msg.data.data[i * 2 + 1] = statusDetail;
      }
    }
    unsigned long elapsed_status = micros() - t0_status;
    char log_buf[128];
    snprintf(log_buf, sizeof(log_buf), "[NUBI] status read 20 servos: %lu us", elapsed_status);
    debug_log(log_buf);
    rcl_publish(&status_publisher, &status_msg, NULL);
  }
}

void status_timer_setup(){
  rclc_timer_init_default(
    &status_timer,
    &support,
    RCL_MS_TO_NS(status_timer_period_ms),   // 2 Hz
    status_timer_callback);
  rclc_executor_add_timer(&executor, &status_timer);
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
    RCL_MS_TO_NS(torque_timer_period_ms),   // 1 Hz
    torque_timer_callback);
  
  rclc_executor_add_timer(&executor, &torque_timer);
}

// --------------------- Timers Callback Functions ---------------------


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

  rclc_publisher_init_default(
    &debug_publisher,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, String),
    "nubi_debug");

  // create executor
  // make sure you change the number to the number of subscribers
  RCCHECK(rclc_executor_init(&executor, &support.context, 5, &allocator));  
  //RCCHECK(rclc_executor_add_subscription(&executor, &subscriber, &msg, &subscription_callback, ON_NEW_DATA));
  leg_cmd_sub_setup();        //1
  upperbody_cmd_sub_setup();  //2
  torque_cmd_sub_setup();     //3
  torque_timer_setup();       //4
  status_timer_setup();       //5

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

  // Round-robin: read ONE leg AND ONE upper servo per loop iteration
  // Legs cycle 0..11, upper cycles 0..6 independently
  {
    unsigned long t0 = micros();
    legs_feedback.data.data[leg_feedback_index] = Herkulex.getAngle(leg_motor_indecies[leg_feedback_index]);
    unsigned long el = micros() - t0;
    char buf[128];
    snprintf(buf, sizeof(buf), "[NUBI] leg[%d] getAngle: %lu us", leg_feedback_index, el);
    debug_log(buf);
    leg_feedback_index++;
    if (leg_feedback_index >= 12) leg_feedback_index = 0;
  }

  {
    unsigned long t0 = micros();
    upperbody_feedback.data.data[upper_feedback_index] = Herkulex.getAngle(upper_motor_indecies[upper_feedback_index]);
    unsigned long el = micros() - t0;
    char buf[128];
    snprintf(buf, sizeof(buf), "[NUBI] upper[%d] getAngle: %lu us", upper_feedback_index, el);
    debug_log(buf);
    upper_feedback_index++;
    if (upper_feedback_index >= 7) upper_feedback_index = 0;
  }

  // Publish feedback
  RCSOFTCHECK(rcl_publish(&leg_pos_feedback_publisher, &legs_feedback, NULL));
  RCSOFTCHECK(rcl_publish(&upperbody_pos_feedback_publisher, &upperbody_feedback, NULL));
  // status is published by status_timer_callback at 3 Hz


  RCCHECK(rclc_executor_spin_some(&executor, RCL_MS_TO_NS(2)));
}