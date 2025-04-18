from kivy.config import Config
Config.set('kivy', 'keyboard_mode', 'systemanddock')
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivymd.toast import toast
from kivy.clock import Clock, mainthread
from kivy.logger import Logger
from kivy.utils import platform
import asyncio, threading
from bleak import BleakClient, BleakScanner
from jnius import autoclass, PythonJavaClass, java_method, cast

# Define BLE UUIDs (must match the Arduino code)
BLE_SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"
BLE_CHARACTERISTIC_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"

colors = {
    "Blue": {"200": "#EEEEFF", "500": "#EEEEFF", "700": "#EEEEFF"},
    "BlueGray": {"200": "##005AAB", "500": "##005AAB", "700": "##005AAB"},
    "Red": {"A200": "#DDD8DD", "A500": "#DDD8DD", "A700": "#DDD8DD"},
    "Light": {"StatusBar": "#E0E0E0", "AppBar": "#202020", "Background": "#EEEEEE", "CardsDialogs": "#FFFFFF", "FlatButtonDown": "#CCCCCC"},
    "Dark": {"StatusBar": "#101010", "AppBar": "#E0E0E0", "Background": "#111111", "CardsDialogs": "#000000", "FlatButtonDown": "#333333"},
}

DEBUG = True
CONFIG_PPR = 800
CONFIG_PITCH = 5

class ScreenSplash(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenSplash, self).__init__(**kwargs)
        Logger.info("Loading ScreenSplash")
        Clock.schedule_interval(self.update_progress_bar, .01)

    def update_progress_bar(self, *args):
        if (self.ids.progress_bar.value + 1) < 100:
            raw_value = self.ids.progress_bar_label.text.split('[')[-1]
            value = raw_value[:-2]
            value = eval(value.strip())
            new_value = value + 1
            self.ids.progress_bar.value = new_value
            self.ids.progress_bar_label.text = 'Loading.. [{:} %]'.format(new_value)
        else:
            self.ids.progress_bar.value = 100
            self.ids.progress_bar_label.text = 'Loading.. [{:} %]'.format(100)
            Clock.schedule_once(lambda dt: setattr(self.screen_manager, 'current', 'screen_home'), 0.5)
            Clock.unschedule(self.update_progress_bar)
            return False

class ScanCallback(PythonJavaClass):
    __javainterfaces__ = ['android/bluetooth/le/ScanCallback']

    def __init__(self, screen_home):
        super().__init__()
        self.screen_home = screen_home

    @java_method('(ILjava/util/List;Landroid/bluetooth/le/ScanResult;)V')
    def onScanResult(self, callbackType, result):
        """Called when a BLE device is found."""
        device = result.getDevice()
        name = device.getName()
        address = device.getAddress()
        self.screen_home.add_ble_device(name, address)

    @java_method('(I)V')
    def onScanFailed(self, errorCode):
        """Called when the scan fails."""
        Logger.error(f"BLE: Scan failed with error code {errorCode}")
        self.screen_home.show_toast(f"BLE scan failed: {errorCode}")


class ScreenHome(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenHome, self).__init__(**kwargs)
        self.ble_client = None
        self.ble_service = None
        self.ble_devices = []
        self.selected_device = None

    def detect_ble_devices(self):
        """Start BLE scanning."""
        self.ble_devices = []  # Clear the list of devices
        if platform == "android":
            threading.Thread(target=self._start_ble_scan_android).start()
        elif platform in ("win", "linux", "macosx"):
            threading.Thread(target=self._start_ble_scan_desktop).start()

    def _start_ble_scan_android(self):
        """Perform BLE scanning using Android's BluetoothLeScanner."""
        try:
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            BluetoothManager = autoclass('android.bluetooth.BluetoothManager')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')

            # Get the Bluetooth adapter
            activity = PythonActivity.mActivity
            context = activity.getApplicationContext()
            bluetooth_manager = cast(BluetoothManager, context.getSystemService("bluetooth"))
            bluetooth_adapter = bluetooth_manager.getAdapter()

            if not bluetooth_adapter.isEnabled():
                Logger.error("BLE: Bluetooth is not enabled.")
                self.show_toast("Please enable Bluetooth.")
                return

            # Get the BluetoothLeScanner
            bluetooth_le_scanner = bluetooth_adapter.getBluetoothLeScanner()
            if not bluetooth_le_scanner:
                Logger.error("BLE: Bluetooth LE Scanner is not available.")
                self.show_toast("BLE Scanner not available.")
                return

            # Start scanning
            self.scan_callback = ScanCallback(self)
            Logger.info("BLE: Starting BLE scan...")
            bluetooth_le_scanner.startScan(None, self.scan_callback)

            # Stop scanning after 10 seconds
            Clock.schedule_once(lambda dt: bluetooth_le_scanner.stopScan(None), 10)

        except Exception as e:
            Logger.error(f"BLE: Failed to scan for devices: {e}")
            self.show_toast("Failed to scan for BLE devices.")

    def _start_ble_scan_desktop(self):
        async def scan():
            try:
                self.ble_devices = await BleakScanner.discover()
                Logger.info(f"Found BLE devices: {self.ble_devices}")
                self.update_ble_devices_menu()
                self.show_toast(f"Found {len(self.ble_devices)} BLE devices")
            except Exception as e:
                Logger.error(f"Failed to scan for BLE devices: {e}")
                self.show_toast("Failed to scan for BLE devices")
        asyncio.run(scan())

    @mainthread
    def add_ble_device(self, name, address):
        """Add a BLE device to the list."""
        if name is None:
            name = "Unknown Device"
        self.ble_devices.append({"name": name, "address": address})
        Logger.info(f"BLE: Adding device - Name: {name}, Address: {address}")

    @mainthread
    def update_ble_devices_menu(self):
        """Update the dropdown menu with the scanned BLE devices."""
        Logger.info(f"BLE: Updating dropdown menu with {len(self.ble_devices)} devices")
        menu_items = [
            {
                "text": device.name if device.name else device.address,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=device: self.select_ble_device(x),
            }
            for device in self.ble_devices
        ]
        self.menu = MDDropdownMenu(
            caller=self.ids.com_port_button,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()

    @mainthread
    def show_toast(self, message):
        """Show a toast message."""
        toast(message)

    def open_com_port_menu(self):
        self.detect_ble_devices()
        self.show_toast("Scanning for BLE devices...")
        
    def select_ble_device(self, device):
        """Handle BLE device selection."""
        self.selected_device = device
        self.ids.com_port_button.text = device.name if device.name else device.address
        self.menu.dismiss()

    def connect_ble(self):
        if self.selected_device:
            threading.Thread(target=self._connect_ble).start()

    def _connect_ble(self):
        async def connect():
            self.ble_client = BleakClient(self.selected_device)
            try:
                await self.ble_client.connect()
                Logger.info(f"Connected to {self.selected_device.name}!")
                self.show_toast(f"Connected to {self.selected_device.name}")
            except Exception as e:
                Logger.error(f"Failed to connect to {self.selected_device.name}: {e}")
                self.show_toast(f"Failed to connect to {self.selected_device.name}")
        asyncio.run(connect())

    async def send_ble_command(self, command):
        if self.ble_client and self.ble_client.is_connected:
            try:
                await self.ble_client.write_gatt_char(BLE_CHARACTERISTIC_UUID, command.encode())
                Logger.info(f"Sent command: {command}")
            except Exception as e:
                Logger.error(f"Failed to send command: {e}")
                self.show_toast("Failed to send command")

    def act_home(self):
        if self.ble_client:
            asyncio.run(self.send_ble_command("HOME\n"))
            self.show_toast("Moving to Home Position")

    def act_up(self):
        if self.ble_client:
            asyncio.run(self.send_ble_command("UP\n"))
            self.show_toast("Moving Up")

    def act_down(self):
        if self.ble_client:
            asyncio.run(self.send_ble_command("DN\n"))
            self.show_toast("Moving Down")

    def act_stop(self):
        if self.ble_client:
            asyncio.run(self.send_ble_command("STOP\n"))

    def act_start(self):
        if self.ble_client:
            set_point_pos = self.ids.tx_field.text
            set_point_pulse = int(float(set_point_pos) * CONFIG_PPR / CONFIG_PITCH)
            if set_point_pulse > 0:
                asyncio.run(self.send_ble_command(f"{set_point_pulse}\n"))
                self.show_toast(f"Moving to position {set_point_pos} mm")

class RootScreen(ScreenManager):
    pass

class GravityMeterApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self):
        Window.bind(on_rotate=self.on_rotation)
        if platform == "android":
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.BLUETOOTH,
                Permission.BLUETOOTH_ADMIN,
                Permission.BLUETOOTH_CONNECT,
                Permission.BLUETOOTH_SCAN,
                Permission.ACCESS_FINE_LOCATION
            ])
            if not self.is_bluetooth_supported():
                Logger.error("App: Bluetooth is not supported on this device.")
                self.show_toast("Bluetooth is not supported on this device.")
                return None

            if not self.is_bluetooth_enabled():
                Logger.info("App: Bluetooth is not enabled. Prompting user to enable it.")
                self.enable_bluetooth()
        else:
            Logger.info("App: Running on non-Android platform, skipping permission requests.")

        self.theme_cls.colors = colors
        self.theme_cls.primary_palette = "BlueGray"
        self.theme_cls.accent_palette = "Blue"
        self.icon = 'asset/Logo_Main.png'
        Window.allow_screensaver = True
        # Window.size = (1366, 768)
        # Window.size = (480, 1280)
        Window.fullscreen = 'auto'
        Window.borderless = True
        

        Builder.load_file('main.kv')
        return RootScreen()

    def is_bluetooth_supported(self):
        BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
        adapter = BluetoothAdapter.getDefaultAdapter()
        return adapter is not None

    def is_bluetooth_enabled(self):
        BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
        adapter = BluetoothAdapter.getDefaultAdapter()
        return adapter is not None and adapter.isEnabled()

    def enable_bluetooth(self):
        Intent = autoclass('android.content.Intent')
        Settings = autoclass('android.provider.Settings')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')

        intent = Intent(Settings.ACTION_BLUETOOTH_SETTINGS)
        current_activity = PythonActivity.mActivity
        current_activity.startActivity(intent)

    def on_rotation(self, window, rotation):
        """rotation will be one of: 0, 90, 180, 270"""
        print(f"Device rotated to: {rotation} degrees")

if __name__ == '__main__':
    GravityMeterApp().run()