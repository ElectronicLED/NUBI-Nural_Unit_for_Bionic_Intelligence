#include <micro_ros_arduino.h>

#include <Herkulex.h>

#include <stdio.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>

#include <std_msgs/msg/int16.h>
#include <std_msgs/msg/int16_multi_array.h>


rcl_subscription_t subscriber;
rcl_publisher_t publisher;
//std_msgs__msg__Int16 msg;
std_msgs__msg__Int16MultiArray legs_command;
std_msgs__msg__Int16MultiArray legs_feedback;
// int test[12];

rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;
rcl_timer_t timer;

#define RCCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){error_loop();}}
#define RCSOFTCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){}}

int n=18;

const uint leg_motor_indecies[12] = {1,2,3,4,5,6,7,8,9,10,11,12};



void error_loop(){
  while(1){
    digitalWrite(PB6, !digitalRead(PB6));
    delay(100);
  }
}

void legs_cmd_callback(const void * msgin){
  const std_msgs__msg__Int16MultiArray * msg = (const std_msgs__msg__Int16MultiArray *)msgin;
  
  for(int i = 0; i<12;i++){
    Herkulex.moveOneAngle(leg_motor_indecies[i], msg->data.data[i], 1000, LED_BLUE);
    // test[0]=msg->data.data[0];
    // test[1]=msg->data.
    //Serial.println(test);
  }
}

// void subscription_callback(const void * msgin)
// {
//   const std_msgs__msg__Int16 * msg = (const std_msgs__msg__Int16 *)msgin;
//   //The print is not working
//   Serial.println(msg->data);
//   if (msg->data == 90)
//   {
//     digitalWrite(LED_BUILTIN, HIGH);
//     delay(250);
//     digitalWrite(LED_BUILTIN, LOW);
//   }
//   Herkulex.moveOneAngle(n, msg->data, 1000, LED_BLUE); //move motor  
//   delay(1000);
//   Serial.println("Servo angle:");
//   Serial.println(Herkulex.getAngle(n));
// }

void setup() {
  pinMode(LED_BUILTIN,OUTPUT);

  set_microros_transports();
  // put your pinMode definitions here

  delay(2000);
  allocator = rcl_get_default_allocator();

  //create init_options
  RCCHECK(rclc_support_init(&support, 0, NULL, &allocator));
  // create node
  RCCHECK(rclc_node_init_default(&node, "NUBI_STM_NODE", "", &support));

  // create subscriber
  RCCHECK(rclc_subscription_init_default(
    &subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "legs_command"));

  // create publisher
  RCCHECK(rclc_publisher_init_default(
    &publisher,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int16MultiArray),
    "legs_feedback"));

  // create executor
  RCCHECK(rclc_executor_init(&executor, &support.context, 1, &allocator));  
  //RCCHECK(rclc_executor_add_subscription(&executor, &subscriber, &msg, &subscription_callback, ON_NEW_DATA));
  RCCHECK(rclc_executor_add_subscription(&executor, &subscriber, &legs_command, &legs_cmd_callback, ON_NEW_DATA));

  //Servo initialization
  //Serial.begin(115200); //and it works with sirial monitor !!
  delay(2000);  //a delay to have time for serial monitor opening
  Herkulex.begin(115200,PA9,PA10); //open serial with rx=PB7 and tx=PB6 
  Herkulex.reboot(n); //reboot first motor
  delay(500); 
  Herkulex.initialize(); //initialize motors
  delay(200);  
}

void loop() {
  // put your main code here, to run repeatedly:

  delay(100);
  RCCHECK(rclc_executor_spin_some(&executor, RCL_MS_TO_NS(100)));
}
