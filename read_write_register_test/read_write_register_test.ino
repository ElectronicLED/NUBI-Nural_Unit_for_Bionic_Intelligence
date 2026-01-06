#include "Herkulex.h"

// PID Register Addresses (RAM)
#define ADDR_KP 0x018
#define ADDR_KD 0x1A
#define ADDR_KI 0x1C

int servoID = 1; // Default Herkulex ID is 253 (0xFD)

void setup() {
  Serial.begin(115200);
  delay(100);
  
  // Initialize Herkulex (Change 115200 to 57600 if using SoftwareSerial on UNO)
  Herkulex.begin(115200,PA9,PA10); 
  Herkulex.initialize();
  delay(500);

  Serial.println("--- Herkulex PID Tuner ---");

  // 1. READ Current PID Values
  readPID();

  // 2. EDIT PID Values (Example: Increase P slightly)
  // Note: Kp is stored in RAM. It resets to default when power is lost.
  // To save permanently, use writeRegistryEEP instead (but be careful of write cycles).
  
  int newKp = 254; 
  int newKd = 6500;
  
  Serial.print("Writing new Kp: "); Serial.println(newKp);
  writePID(ADDR_KP, newKp);
  
  // Serial.print("Writing new Kd: "); Serial.println(newKd);
  // writePID(ADDR_KD, newKd);

  // delay(100);

  // // 3. Verify the change
  // Serial.println("--- Verifying New Values ---");
  // readPID();
}

void loop() {
  // Empty loop
}

void readPID() {
  // Use the new function we added to the library
  int p = Herkulex.readRegistryRAM(servoID, ADDR_KP);
  int d = Herkulex.readRegistryRAM(servoID, ADDR_KD);
  int i = Herkulex.readRegistryRAM(servoID, ADDR_KI);

  Serial.print("Current PID -> P: ");
  Serial.print(p);
  Serial.print(" | D: ");
  Serial.print(d);
  Serial.print(" | I: ");
  Serial.println(i);
}

void writePID(int regAddress, int value) {
  // The library's writeRegistryRAM writes 1 byte. 
  // PID values are 2 bytes (Int), so we must write LSB and MSB separately.
  
  byte lsb = value & 0xFF;
  byte msb = (value >> 8) & 0xFF;

  // Write LSB to address
  Herkulex.writeRegistryRAM(servoID, regAddress, lsb);
  delay(5);
  // Write MSB to address + 1
  Herkulex.writeRegistryRAM(servoID, regAddress + 1, msb);
  delay(5);
}