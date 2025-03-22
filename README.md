# Gravity Meter App
 Embedded application for Gravity Meter Automatic Positioner

## Overview
This project is a KivyMD application designed for a gravity meter. It utilizes Bluetooth Low Energy (BLE) for device communication and provides a user-friendly interface for controlling the gravity meter.

## Project Structure
- **main.py**: Contains the main application logic, including classes for different screens and methods for BLE device management.
- **main.kv**: Defines the user interface layout using Kivy language.
- **buildozer.spec**: Configuration file for Buildozer to compile the application into an Android APK.
- **asset/Logo_Main.png**: Image asset used as the application icon.

## Setup Instructions
1. **Install Dependencies**: Ensure you have Python and pip installed. Then, install Kivy and KivyMD:
   ```
   pip install kivy kivymd bleak
   ```

2. **Build the APK**:
   - Install Buildozer:
     ```
     pip install buildozer
     ```
   - Navigate to the project directory and run:
     ```
     buildozer init
     ```
   - Edit the `buildozer.spec` file to configure your application settings.
   - Build the APK:
     ```
     buildozer -v android debug
     ```

3. **Run the Application**: Once the APK is built, you can install it on your Android device.

## Usage
- Launch the application to start scanning for BLE devices.
- Select a device from the dropdown menu to connect.
- Use the provided buttons to send commands to the gravity meter.

## License
This project is licensed under the MIT License. See the LICENSE file for more details.