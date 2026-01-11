#include "Herkulex.h"

int n=19; //motor ID - verify your ID !!!!

int angle = 0;

void setup()  
{
  
  Serial.begin(9600); //and it works with sirial monitor !!
  pinMode(LED_BUILTIN, OUTPUT);
  delay(2000);  //a delay to have time for serial monitor opening
  Herkulex.begin(115200,PA9,PA10); //open serial with rx=PB7 and tx=PB6 
  for(int i=0; i<n;i++){
  Herkulex.reboot(i); //reboot first motor
  delay(50);
  } 
  Herkulex.initialize(); //initialize motors
  delay(200);  
}

void loop(){
  Serial.println("-----------------------");
  digitalWrite(LED_BUILTIN, !digitalRead(LED_BUILTIN)); 
  for(int i=0; i<=n;i++){
    Serial.print("Servo ");
    Serial.print(i);
    Serial.print(" ");
    Serial.println(Herkulex.getAngle(i));
  }
  Serial.println("______");
  for(int i=0; i<=n;i++){
    // Serial.print("Moving Servo: ");
    // Serial.println(i);
    Herkulex.moveOneAngle(i, angle,500,LED_BLUE);
    //delay(200);
  }
  angle = -angle;
  // Herkulex.moveOneAngle(n, -100, 1000, LED_BLUE); //move motor with 300 speed  
  // delay(1200);
  // Serial.println("100");
  // digitalWrite(LED_BUILTIN, LOW); 
  // Herkulex.moveOneAngle(n, 100, 1000, LED_BLUE); //move motor with 300 speed  
  // delay(1200);
  delay(1000);
  
}


