#include <AccelStepper.h>
#include <ArduinoBLE.h>

// Define pins for the stepper motor driver and limit switch
#define STEP_PIN 12
#define DIR_PIN 10
#define LIMIT_SWITCH_PIN 4 // Pin connected to the limit switch

// Create an AccelStepper object
AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);

BLEService stepperService("19B10000-E8F2-537E-4F6C-D104768A1214"); // Custom UUID
BLEStringCharacteristic commandCharacteristic("19B10001-E8F2-537E-4F6C-D104768A1214", BLERead | BLEWrite, 20); // Max 20 bytes
// Variables to store the desired position and serial input
long desiredPosition = 0;
String serialInput = "";
bool homing = false; // Flag to indicate homing process
bool manual_up = false; // Flag to indicate manual up
bool manual_dn = false; // Flag to indicate manual down

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
  // while (!Serial);

  // Initialize BLE
  if (!BLE.begin()) {
    Serial.println("Failed to initialize BLE!");
    while (1);
  }

  // Set the BLE device name
  BLE.setLocalName("GRAVI_BT");
  BLE.setAdvertisedService(stepperService);

  // Add the characteristic to the service
  stepperService.addCharacteristic(commandCharacteristic);

  // Add the service to BLE
  BLE.addService(stepperService);

  // Start advertising
  BLE.advertise();
  Serial.println("Bluetooth device is ready to pair!");
  Serial.println("Waiting for connections...");

  // Set the maximum speed and acceleration of the stepper motor
  stepper.setMaxSpeed(1000);    // Adjust as needed
  stepper.setAcceleration(500); // Adjust as needed

  // Set the limit switch pin as input with pull-up resistor
  pinMode(LIMIT_SWITCH_PIN, INPUT_PULLUP);
}

void loop() {
  // Check for BLE connections
  BLEDevice central = BLE.central();  
  // Check if data is available from the Serial Monitor
  // If a central device is connected
  if (central) {
    Serial.print("Connected to central: ");
    Serial.println(central.address());

    // While the central is connected
    while (central.connected()) {
      // Check if the command characteristic has been written to
      if (commandCharacteristic.written()) {
        serialInput = commandCharacteristic.value(); // Read the incoming data
        desiredPosition = serialInput.toInt();
        Serial.print("Received command: ");
        Serial.println(serialInput);
        // If the incoming character is a newline, process the input
        // if (incomingChar == '\n') {
          if (serialInput == "HOME\n") {
            // Start homing process
            homing = true;
            Serial.print("Homing: ");
            Serial.println(homing);
            stepper.setSpeed(1000); // Move backward at a constant speed
          } else if (serialInput == "UP\n") {
            // Start manual up process
            manual_up = true;
            Serial.print("Manual Up: ");
            Serial.println(manual_up);            
            stepper.setSpeed(-1000); // Move forward at a constant speed
          } else if (serialInput == "DN\n") {
            // Start manual down process
            manual_dn = true;
            Serial.print("Manual Down: ");
            Serial.println(manual_dn);    
            stepper.setSpeed(1000); // Move backward at a constant speed
          } else if (desiredPosition > 0) {
            Serial.print("Desired Pos: ");
            Serial.println(desiredPosition);               
            stepper.moveTo(-desiredPosition); // Move the stepper to the desired position
          }
        //   serialInput = ""; // Clear the input string
        // } else {
        //   serialInput += incomingChar; // Append the character to the input string
        // }
      }

      // Homing process
      if (homing) {
        if (digitalRead(LIMIT_SWITCH_PIN) == LOW) { // Limit switch is pressed (LOW because of pull-up)
          stepper.setCurrentPosition(0); // Set the current position as 0
          stepper.stop(); // Stop the motor
          homing = false; // End homing process
          Serial.println("Homing complete. Position set to 0.");
        } else {
          stepper.runSpeed(); // Continue moving backward
        }
      } else if (manual_up) {
          stepper.setCurrentPosition(0);
          stepper.moveTo(-2000);
          stepper.run(); // moving forward
          manual_up = false;
      } else if (manual_dn) {
          stepper.setCurrentPosition(0);
          stepper.moveTo(2000);
          stepper.run(); // moving backward
          manual_dn = false;
      } else {
        // Run the stepper motor to the desired position
        stepper.run();
      }
    }
        // When the central disconnects
    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
  }

}