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
#define NUM_STD_SERVOS 4
#define NUM_LEGS 12
#define NUM_UPPDERBODY 7
// ------------------- Index protocol (status_command / status_response) --------
// PC -> STM (status_command data[0]):
//   0 = request status array
//   2 = torque change  (data[1]: 1=ON, 0=OFF)
//   3 = request torque status array
//   6 = reset error
//   7 = reinitialize servos (reboot all + clearError + ACK + torqueON)
//   8 = move one servo  data[1]=servo_id  data[2]=angle(deg, int16)  data[3]=play_time(ms)
// STM -> PC (status_response data[0]):
//   1 = status array    (data[1..40] = 20 × [statusError, statusDetail])
//   5 = torque array    (data[1..20] = 20 × torque byte)
#define CMD_REQUEST_STATUS   0
#define CMD_TORQUE_SET       2
#define CMD_REQUEST_TORQUE   3
#define CMD_RESET_ERROR      6
#define CMD_REINITIALIZE     7
#define CMD_MOVE_ONE         8
#define RESP_STATUS_ARRAY    1
#define RESP_TORQUE_ARRAY    5
#define STATUS_ARRAY_SIZE     41   // index byte + up to 40 data bytes
// number of motors
int n=20;


const uint leg_motor_indecies[NUM_LEGS] = {16,6,7,8,10,9,17,18,12,13,15,14};
const uint upper_motor_indecies[NUM_UPPDERBODY] = {0,1,2,3,4,11,19};
// Standard (non-Herkulex) servos — pin order matches upperbody_command.data [7..10]
const int std_servo_pins[NUM_STD_SERVOS] = {PB13, PB14, PB15, PA8};
Servo std_servo[NUM_STD_SERVOS];

// ------------------- micro-ROS objects defined once -------------------
rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;

// ------------------- micro-ROS Subscribers object -------------------
rcl_subscription_t leg_command_subscriber;
rcl_subscription_t upperbody_command_subscriber;
rcl_subscription_t status_command_subscriber;
rcl_subscription_t gripper_command_subscriber;
rcl_subscription_t color_cmd_subscriber;

// ------------------- micro-ROS Publishers object -------------------
rcl_publisher_t leg_pos_feedback_publisher;
rcl_publisher_t upperbody_pos_feedback_publisher;
rcl_publisher_t status_response_publisher;
rcl_publisher_t color_feedback_publisher;
rcl_publisher_t debug_publisher;


// -------------------Timer objects -------------------
rcl_timer_t color_timer;

//Subscriber messages
std_msgs__msg__Int16MultiArray legs_command;
std_msgs__msg__Int16MultiArray upperbody_command;
std_msgs__msg__Int16MultiArray status_command;
std_msgs__msg__Int16MultiArray gripper_command;
std_msgs__msg__Int16MultiArray color_command;

//Publisher messages
std_msgs__msg__Int16MultiArray legs_feedback;
std_msgs__msg__Int16MultiArray upperbody_feedback;
std_msgs__msg__Int16MultiArray status_response;
std_msgs__msg__Int16MultiArray color_feedback;

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

// loops on servos by turn — separate indices for legs and upper body
int leg_feedback_index = 0;
int upper_feedback_index = 0;
#define FEEDBACK_TOTAL 19   // 12 legs + 7 upper (kept for reference)


// statusError/statusDetail are now local to status_cmd_callback


// macros to check if any function returns anything other than RCL_RET_OK othwerwise stick to error or pass
#define RCCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){error_loop();}}
// same check but without sticking in error loop
#define RCSOFTCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){}}


void error_loop(){
  // NOTE: do NOT call debug_log here — debug_publisher may not be initialized yet.
  while(1){
    digitalWrite(PC13, !digitalRead(PC13));
    delay(100);
  }
}

// --------------------- Subsribers Callback Functions ---------------------
void legs_cmd_callback(const void * msgin){
  // Queue all 12 leg servos then fire simultaneously with actionAll
  int i = 0;
  for(; i<NUM_LEGS;i++){
    Herkulex.moveAllAngle(leg_motor_indecies[i], legs_command.data.data[i], LED_BLUE);
  }
  //always take last index as playtime
  Herkulex.actionAll(legs_command.data.data[i]);  // 500ms execution time — reduce if hardware allows
}

void upperbody_cmd_callback(const void * msgin){
  // Queue all 7 Herkulex servos then fire simultaneously with actionAll
  int i = 0;
  for(; i<NUM_UPPDERBODY; i++){
    Herkulex.moveAllAngle(upper_motor_indecies[i], upperbody_command.data.data[i], LED_BLUE);
  }
  // i == NUM_UPPDERBODY (7) — next 4 values are standard servo angles (-150..+150 → 0..180)
  for(int j = 0; j < NUM_STD_SERVOS; j++){
    int angle = (int)upperbody_command.data.data[i + j];

    int servo_pos = constrain(angle, 0, 180);
    std_servo[j].write(servo_pos);
  }
  // last element (data[11]) is playtime for Herkulex actionAll
  Herkulex.actionAll(upperbody_command.data.data[i + NUM_STD_SERVOS]);
}

void status_cmd_callback(const void * msgin){
  int16_t idx = status_command.data.data[0];

  // ── Print index and indicated action ──
  char log_buf[128];
  const char* action_str = "unknown";
  switch(idx){
    case CMD_REQUEST_STATUS: action_str = "request status array";  break;
    case CMD_TORQUE_SET:     action_str = "torque set";             break;
    case CMD_REQUEST_TORQUE: action_str = "request torque array";  break;
    case CMD_RESET_ERROR:    action_str = "reset error";            break;
    case CMD_REINITIALIZE:   action_str = "reinitialize servos";    break;
    case CMD_MOVE_ONE:       action_str = "move one servo";         break;
  }
  snprintf(log_buf, sizeof(log_buf), "[NUBI] received index %d -> %s", (int)idx, action_str);
  debug_log(log_buf);

  if(idx == CMD_REQUEST_STATUS){
    unsigned long t0 = micros();
    for(int i = 0; i < 20; i++){
      byte statusError = 0, statusDetail = 0;
      byte result = Herkulex.stat(i, statusError, statusDetail);
      if(result != (byte)-1 && result != (byte)-2){
        status_response.data.data[i * 2 + 1] = statusError;
        status_response.data.data[i * 2 + 2] = statusDetail;
      }
    }
    unsigned long elapsed = micros() - t0;
    snprintf(log_buf, sizeof(log_buf), "[NUBI] status read 20 servos: %lu us", elapsed);
    debug_log(log_buf);
    status_response.data.data[0] = RESP_STATUS_ARRAY;
    status_response.data.size = STATUS_ARRAY_SIZE;
    rcl_publish(&status_response_publisher, &status_response, NULL);
  }
  else if(idx == CMD_TORQUE_SET){
    int16_t torque_on = status_command.data.data[1];
    if(torque_on == 1){
      Herkulex.torqueON(BROADCAST_ID);
      debug_log("[NUBI] torqueON applied");
    } else {
      Herkulex.torqueOFF(BROADCAST_ID);
      debug_log("[NUBI] torqueOFF applied");
    }
    // Auto-publish torque state immediately after applying change
    unsigned long t0_tq = micros();
    for(int i = 0; i < 20; i++){
      byte tq = Herkulex.getTorque(i);
      status_response.data.data[i + 1] = (tq == 0x60) ? 1 : 0;
    }
    unsigned long elapsed_tq = micros() - t0_tq;
    snprintf(log_buf, sizeof(log_buf), "[NUBI] torque auto-publish after set: %lu us", elapsed_tq);
    debug_log(log_buf);
    status_response.data.data[0] = RESP_TORQUE_ARRAY;
    status_response.data.size = STATUS_ARRAY_SIZE;
    rcl_publish(&status_response_publisher, &status_response, NULL);
  }
  else if(idx == CMD_REQUEST_TORQUE){
    unsigned long t0 = micros();
    for(int i = 0; i < 20; i++){
      byte tq = Herkulex.getTorque(i);
      status_response.data.data[i + 1] = (tq == 0x60) ? 1 : 0;
    }
    unsigned long elapsed = micros() - t0;
    snprintf(log_buf, sizeof(log_buf), "[NUBI] torque read 20 servos: %lu us", elapsed);
    debug_log(log_buf);
    status_response.data.data[0] = RESP_TORQUE_ARRAY;
    status_response.data.size = STATUS_ARRAY_SIZE;
    rcl_publish(&status_response_publisher, &status_response, NULL);
  }
  else if(idx == CMD_RESET_ERROR){
    Herkulex.clearError(BROADCAST_ID);
    debug_log("[NUBI] clearError applied");
  }
  else if(idx == CMD_MOVE_ONE){
    int16_t servo_id  = status_command.data.data[1];
    int16_t angle     = status_command.data.data[2];
    int16_t play_time = status_command.data.data[3];
    Herkulex.moveOneAngle(servo_id, (float)angle, (int)play_time, LED_BLUE);
    char mv_buf[64];
    snprintf(mv_buf, sizeof(mv_buf), "[NUBI] moveOne id=%d angle=%d t=%d", (int)servo_id, (int)angle, (int)play_time);
    debug_log(mv_buf);
  }
  else if(idx == CMD_REINITIALIZE){
    debug_log("[NUBI] reinitialize: rebooting all servos...");
    for(int i = 0; i < n; i++){
      Herkulex.reboot(i);
      delay(50);
    }
    delay(1500);  // wait for all servos to fully boot
    Herkulex.initialize();  // clearError + ACK(1) + torqueON
    delay(200);
    Herkulex.clearError(BROADCAST_ID);
    delay(50);
    Herkulex.torqueON(BROADCAST_ID);
    debug_log("[NUBI] reinitialize complete");
  }
}



// --------------------- Subsribers Setup Functions ---------------------
void leg_cmd_sub_setup(){
  static int16_t memory_buffer[13]; 
  legs_command.data.capacity = 13;
  legs_command.data.data = memory_buffer;
  legs_command.data.size = 0;

  RCCHECK(rclc_subscription_init_best_effort(
    &leg_command_subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "legs_command"));
  
  RCCHECK(rclc_executor_add_subscription(&executor, &leg_command_subscriber, &legs_command, &legs_cmd_callback, ON_NEW_DATA));
}

void upperbody_cmd_sub_setup(){
  // 7 Herkulex + 4 std servo + 1 playtime = 12
  static int16_t memory_buffer1[12]; 
  upperbody_command.data.capacity = 12;
  upperbody_command.data.data = memory_buffer1;
  upperbody_command.data.size = 0;

  RCCHECK(rclc_subscription_init_best_effort(
    &upperbody_command_subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "upperbody_command"));
  
  RCCHECK(rclc_executor_add_subscription(&executor, &upperbody_command_subscriber, &upperbody_command, &upperbody_cmd_callback, ON_NEW_DATA));
}

void status_cmd_sub_setup(){
  static int16_t status_cmd_buffer[STATUS_ARRAY_SIZE];
  status_command.data.capacity = STATUS_ARRAY_SIZE;
  status_command.data.data     = status_cmd_buffer;
  status_command.data.size     = 0;

  RCCHECK(rclc_subscription_init_best_effort(
    &status_command_subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "status_command"));

  RCCHECK(rclc_executor_add_subscription(&executor, &status_command_subscriber, &status_command, &status_cmd_callback, ON_NEW_DATA));
}



// Status and torque are now driven by GUI requests (status_command).
// No periodic publish timers needed.


void setup() {
  pinMode(LED_BUILTIN,OUTPUT);

  // NOTE: std_servo.attach() must NOT be called before set_microros_transports().
  // PA8/PB13-15 use TIM1 which conflicts with micro-ROS transport init on STM32.
  // Attach is done after all micro-ROS setup below.

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
  // Initialised to 1004 (the "no power" sentinel) so the GUI shows "--" for every
  // servo slot until a real reading arrives. See plans/no-power-sentinel-init.md
  static int16_t feedback_buffer[12];
  for(int i = 0; i < 12; i++) feedback_buffer[i] = 1004;
  // Link the buffer to the message struct
  legs_feedback.data.capacity = 12;
  legs_feedback.data.data = feedback_buffer;
  legs_feedback.data.size = 12; // IMPORTANT: Tell ROS how many items you are sending

  static int16_t feedback_buffer1[7];
  for(int i = 0; i < 7; i++) feedback_buffer1[i] = 1004;
  // Link the buffer to the message struct
  upperbody_feedback.data.capacity = 7;
  upperbody_feedback.data.data = feedback_buffer1;
  upperbody_feedback.data.size = 7; 

  // ── status_response buffer setup ──
  static int16_t status_resp_buffer[STATUS_ARRAY_SIZE];
  memset(status_resp_buffer, 0, sizeof(status_resp_buffer));
  status_response.data.capacity = STATUS_ARRAY_SIZE;
  status_response.data.data     = status_resp_buffer;
  status_response.data.size     = STATUS_ARRAY_SIZE;

  RCCHECK(rclc_publisher_init_best_effort(
    &leg_pos_feedback_publisher,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "legs_feedback"));

  RCCHECK(rclc_publisher_init_best_effort(
    &upperbody_pos_feedback_publisher,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "upperbody_feedback"));

  rclc_publisher_init_best_effort(
    &status_response_publisher,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "status_response");

  rclc_publisher_init_default(
    &debug_publisher,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, String),
    "nubi_debug");

  RCSOFTCHECK(rclc_executor_init(&executor, &support.context, 3, &allocator));  
  leg_cmd_sub_setup();        //1
  upperbody_cmd_sub_setup();  //2
  status_cmd_sub_setup();     //3

  // Attach standard servos AFTER micro-ROS init to avoid TIM1 conflict
  for(int j = 0; j < NUM_STD_SERVOS; j++){
    std_servo[j].attach(std_servo_pins[j]);
  }

  //Servo initialization
  delay(2000);  //a delay to have time for serial monitor opening
  // NOTE: begin(baud, rx_pin, tx_pin) — PA10=RX (servo TX), PA9=TX (servo RX)
  Herkulex.begin(115200, PA10, PA9); //open serial — rx first, then tx
  for(int i=0; i<n; i++){
    Herkulex.reboot(i); //reboot motors
    delay(50);           // increased: servo needs ~40ms to come back after reboot
  }
  delay(1500);           // wait for ALL servos to fully boot before initialize
  
  Herkulex.initialize(); //initialize motors: clearError + ACK(1) + torqueON
  delay(200);
  // Second clearError+torqueON pass to recover any Break-mode servos
  Herkulex.clearError(BROADCAST_ID);
  delay(50);
  Herkulex.torqueON(BROADCAST_ID);
  delay(100);
}


void loop() {
  // put your main code here, to run repeatedly:
  //digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN));

  // Round-robin: read ONE leg AND ONE upper servo per loop iteration
  // Legs cycle 0..11, upper cycles 0..6 independently
  static unsigned long last_pos_log_ms = 0;
  {
    unsigned long t0 = micros();
    float leg_angle = Herkulex.getAngle(leg_motor_indecies[leg_feedback_index]);
    if (leg_angle < 900.0f) {
      // Valid reading — update buffer
      legs_feedback.data.data[leg_feedback_index] = (int16_t)leg_angle;
    } else if (leg_angle >= 1002.0f) {
      // Timeout sentinel (1004) — servo unpowered/disconnected, propagate so GUI shows "--"
      legs_feedback.data.data[leg_feedback_index] = 1004;
    }
    // 999 (checksum noise) falls through: buffer keeps its last good value silently
    unsigned long el = micros() - t0;
    unsigned long now_ms = millis();
    if (now_ms - last_pos_log_ms >= 1000) {
      char buf[128];
      snprintf(buf, sizeof(buf), "[NUBI] leg[%d] getAngle: %lu us", leg_feedback_index, el);
      debug_log(buf);
      last_pos_log_ms = now_ms;
    }
    leg_feedback_index++;
    if (leg_feedback_index >= 12) leg_feedback_index = 0;
  }

  {
    unsigned long t0 = micros();
    float upper_angle = Herkulex.getAngle(upper_motor_indecies[upper_feedback_index]);
    if (upper_angle < 900.0f) {
      // Valid reading — update buffer
      upperbody_feedback.data.data[upper_feedback_index] = (int16_t)upper_angle;
    } else if (upper_angle >= 1002.0f) {
      // Timeout sentinel (1004) — servo unpowered/disconnected, propagate so GUI shows "--"
      upperbody_feedback.data.data[upper_feedback_index] = 1004;
    }
    // 999 (checksum noise) falls through: buffer keeps its last good value silently
    unsigned long el = micros() - t0;
    unsigned long now_ms = millis();
    if (now_ms - last_pos_log_ms >= 1000) {
      char buf[128];
      snprintf(buf, sizeof(buf), "[NUBI] upper[%d] getAngle: %lu us", upper_feedback_index, el);
      debug_log(buf);
      last_pos_log_ms = now_ms;
    }
    upper_feedback_index++;
    if (upper_feedback_index >= 7) upper_feedback_index = 0;
  }

  // Publish feedback
  RCSOFTCHECK(rcl_publish(&leg_pos_feedback_publisher, &legs_feedback, NULL));
  RCSOFTCHECK(rcl_publish(&upperbody_pos_feedback_publisher, &upperbody_feedback, NULL));
  // status_response is published on demand via status_cmd_callback


  RCSOFTCHECK(rclc_executor_spin_some(&executor, RCL_MS_TO_NS(2)));
}