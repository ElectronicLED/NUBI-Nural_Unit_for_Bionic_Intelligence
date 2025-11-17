#include "Herkulex.h"

int n=18; //motor ID - verify your ID !!!!

void setup()  
{
  
  Serial.begin(9600); //and it works with sirial monitor !!
  pinMode(LED_BUILTIN, OUTPUT);
  delay(2000);  //a delay to have time for serial monitor opening
  Herkulex.begin(115200,PA9,PA10); //open serial with rx=PB7 and tx=PB6 
  Herkulex.reboot(n); //reboot first motor
  delay(500); 
  Herkulex.initialize(); //initialize motors
  delay(200);  
}

void loop(){
  Serial.println("-100");
  digitalWrite(LED_BUILTIN, HIGH); 
  Herkulex.moveOneAngle(n, -100, 1000, LED_BLUE); //move motor with 300 speed  
  delay(1200);
  Serial.println("100");
  digitalWrite(LED_BUILTIN, LOW); 
  Herkulex.moveOneAngle(n, 100, 1000, LED_BLUE); //move motor with 300 speed  
  delay(1200);
  
}


