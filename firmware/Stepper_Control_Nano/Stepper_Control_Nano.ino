#include <AccelStepper.h>

// Define pins for the stepper motor driver and limit switch
#define STEP_PIN 12
#define DIR_PIN 10
#define LIMIT_SWITCH_PIN 4 // Pin connected to the limit switch

// Create an AccelStepper object
AccelStepper stepper(AccelStepper::DRIVER, STEP_PIN, DIR_PIN);

// Variables to store the desired position and serial input
long desiredPosition = 0;
String serialInput = "";
bool homing = false; // Flag to indicate homing process
bool manual_up = false; // Flag to indicate manual up
bool manual_dn = false; // Flag to indicate manual down

void setup() {
  // Initialize serial communication
  Serial.begin(9600);
 
  // Set the maximum speed and acceleration of the stepper motor
  stepper.setMaxSpeed(1000);    // Adjust as needed
  stepper.setAcceleration(500); // Adjust as needed

  // Set the limit switch pin as input with pull-up resistor
  pinMode(LIMIT_SWITCH_PIN, INPUT_PULLUP);
}

void loop() {
  // Check if data is available on the serial port
  if (Serial.available() > 0) {
    char incomingChar = Serial.read();

    // If the incoming character is a newline, process the input
    if (incomingChar == '\n') {
      if (serialInput == "HOME") {
        // Start homing process
        homing = true;
        stepper.setSpeed(1000); // Move backward at a constant speed
      } else if (serialInput == "UP") {
        // Start manual up process
        manual_up = true;
        stepper.setSpeed(-1000); // Move forward at a constant speed
      } else if (serialInput == "DN") {
        // Start manual down process
        manual_dn = true;
        stepper.setSpeed(1000); // Move backward at a constant speed
      } else {
        desiredPosition = serialInput.toInt(); // Convert the string to an integer
        stepper.moveTo(-desiredPosition); // Move the stepper to the desired position
      }
      serialInput = ""; // Clear the input string
    } else {
      serialInput += incomingChar; // Append the character to the input string
    }
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
      stepper.moveTo(-1000);
      stepper.run(); // moving forward
      manual_up = false;
  } else if (manual_dn) {
      stepper.setCurrentPosition(0);
      stepper.moveTo(1000);
      stepper.run(); // moving backward
      manual_dn = false;
  } else {
    // Run the stepper motor to the desired position
    stepper.run();
  }
}