#include "Herkulex.h"

void setup()  
{
  int n=0; //set the motor ID
  delay(2000);  //a delay to have time for serial monitor opening
  Serial.begin(115200);    // Open serial communications
  Serial.println("Begin");
  Herkulex.beginSerial1(115200); //open serial port 1 
  Herkulex.reboot(n); //reboot 
  delay(500); 
  Herkulex.initialize(); //initialize motors
  Serial.println("Set Led Green");
  Herkulex.setLed(n,LED_GREEN2); //set the led to green
  Serial.print("Status:"); 
  Serial.println(Herkulex.stat(n)); //verify error code
  Herkulex.end();
}
void loop(){
  for(byte i=0;i<254;i++){
    Serial.print("-----------------------");
    Serial.print(i);
    Serial.println("----------------------"); 
    
    
    Herkulex.beginSerial1(115200); //open serial port 1 
    Herkulex.reboot(i); //reboot 
    delay(500); 
    Herkulex.initialize(); //initialize motors
    Serial.println("Set Led Green");
    Herkulex.setLed(i,LED_GREEN); //set the led to green
    Serial.print("Status:"); 
    Serial.println(Herkulex.stat(i)); //verify error code
    Herkulex.end();
  }
}


