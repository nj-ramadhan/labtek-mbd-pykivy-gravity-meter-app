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

bool manualUp = false;          // Flag to indicate manual up
bool manualDown = false;        // Flag to indicate manual down

bool homingCommand = false;     // Flag to indicate homing process
bool homingComplete = false;    // the current state of the output pin

int buttonState;            // the current reading from the input pin
int lastButtonState = LOW;  // the previous reading from the input pin

unsigned long lastDebounceTime = 0;  // the last time the output pin was toggled
unsigned long debounceDelay = 50;    // the debounce time; increase if the output flickers

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
      
        if (serialInput == "HOME\n") {
          // Start homing process
          homingCommand = true;
          Serial.print("Homing: ");
          Serial.println(homingCommand);
          stepper.setSpeed(1000); // Move backward at a constant speed
        } else if (serialInput == "UP\n") {
          // Start manual up process
          manualUp = true;
          Serial.print("Manual Up: ");
          Serial.println(manualUp);            
          stepper.setSpeed(-1000); // Move forward at a constant speed
        } else if (serialInput == "DN\n") {
          // Start manual down process
          manualDown = true;
          Serial.print("Manual Down: ");
          Serial.println(manualDown);    
          stepper.setSpeed(1000); // Move backward at a constant speed
        } else if (desiredPosition > 0) {
          Serial.print("Desired Pos: ");
          Serial.println(desiredPosition);               
          stepper.moveTo(-desiredPosition); // Move the stepper to the desired position
        }
      }

      int reading = digitalRead(LIMIT_SWITCH_PIN);
      // If the switch changed, due to noise or pressing:
      if (reading != lastButtonState) {
        // reset the debouncing timer
        lastDebounceTime = millis();
      }

      if ((millis() - lastDebounceTime) > debounceDelay) {
        // whatever the reading is at, it's been there for longer than the debounce
        // delay, so take it as the actual current state:

        // if the button state has changed:
        if (reading != buttonState) {
          buttonState = reading;

          if (buttonState == LOW) {
            homingComplete = true;
          }
          else{
            homingComplete = false;
          }
        }
      }
      lastButtonState = reading;

      // Homing process
      if (homingCommand) {
        if (homingComplete) { // Limit switch is pressed (LOW because of pull-up)
          stepper.setCurrentPosition(0); // Set the current position as 0
          stepper.stop(); // Stop the motor
          homingCommand = false; // End homing process
          Serial.println("Homing complete. Position set to 0.");
        } else {
          stepper.runSpeed(); // Continue moving backward
        }
      } else if (manualUp) {
          stepper.setCurrentPosition(0);
          stepper.moveTo(-2000);
          stepper.run(); // moving forward
          manualUp = false;
      } else if (manualDown) {
          stepper.setCurrentPosition(0);
          stepper.moveTo(2000);
          stepper.run(); // moving backward
          manualDown = false;
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