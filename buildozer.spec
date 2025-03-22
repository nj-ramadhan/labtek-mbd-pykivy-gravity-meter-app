[app]
# (str) Title of your application
title = Gravity Meter App

# (str) Package name
package.name = gravitymeter

# (str) Package domain (unique, usually your reverse domain)
package.domain = com.unt_gravitymeter

# (str) Source code where your main.py is located
source.dir = .

# (str) Main Python file
source.main = main.py

# (str) Application version
version = 1.1

# (str) Supported orientation (one of: landscape, portrait, all)
orientation = landscape

# (list) Permissions required by the app
android.permissions = BLUETOOTH, BLUETOOTH_ADMIN, BLUETOOTH_CONNECT, BLUETOOTH_SCAN, INTERNET, ACCESS_FINE_LOCATION

# (str) Package the application icon
icon.filename = assets/images/Logo_Main.png

# (list) Additional source files to include (e.g., .kv files)
source.include_exts = py, kv, png, jpg, jpeg, gif

# (list) Requirements for the app (Python modules, libraries)
requirements = python3, kivy, kivymd, bleak, typing_extensions, pyjnius

# (str) Presplash image
presplash.filename = assets/images/Logo_Main.png

# (str) Fullscreen mode (1 for fullscreen, 0 for windowed)
fullscreen = 1

# (str) Android API level to use
android.api = 33

# (str) Minimum Android API level supported
android.minapi = 26

# (str) Android NDK version to use
android.ndk = 25c

# (str) Android architecture to support
android.archs = arm64-v8a, armeabi-v7a

# (bool) Enable Android logcat output
log_level = 2

# (str) Build type (debug or release)
debug = 1

[buildozer]
# (str) Command to run after building the APK
log_level = 2
warn_on_root = 1