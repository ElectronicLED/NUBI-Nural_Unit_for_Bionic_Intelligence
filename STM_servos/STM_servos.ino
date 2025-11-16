#include "Herkulex.h"

int n=18; //motor ID - verify your ID !!!!

void setup()  
{
  delay(2000);  //a delay to have time for serial monitor opening
  Herkulex.beginSerial1(57600,PA9,PA10); //open serial with rx=PB7 and tx=PB6 
  Herkulex.reboot(n); //reboot first motor
  delay(500); 
  Herkulex.initialize(); //initialize motors
  delay(200);  
}

void loop(){
  Herkulex.moveOneAngle(n, -100, 1000, LED_BLUE); //move motor with 300 speed  
  delay(1200);
 
  Herkulex.moveOneAngle(n, 100, 1000, LED_BLUE); //move motor with 300 speed  
  delay(1200);
  
}


