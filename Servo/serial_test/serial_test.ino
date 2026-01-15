// Check if the serial1 and serial monitor are okay
// connect PA9 to PA10
// the stm will try to talk to itself

void setup() {
  // Serial is for the USB Serial Monitor
  Serial.begin(115200);
  while (!Serial); // Wait for monitor to open

  // Serial1 is for PA9 (TX) and PA10 (RX)
  Serial1.begin(115200); 

  Serial.println("Serial1 Loopback Test Started...");
}

void loop() {
  // Send a test message OUT of the TX pin (PA9)
  Serial1.println("Hello from Serial1");

  // Read anything that comes IN on the RX pin (PA10)
  while (Serial1.available()) {
    char c = Serial1.read();
    Serial.write(c); // Print it to the USB monitor
  }

  delay(1000);
}