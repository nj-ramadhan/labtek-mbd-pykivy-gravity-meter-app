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

# Define BLE UUIDs (must match the Arduino code)
BLE_SERVICE_UUID = "19B10000-E8F2-537E-4F6C-D104768A1214"
BLE_CHARACTERISTIC_UUID = "19B10001-E8F2-537E-4F6C-D104768A1214"
DEBUG = True
CONFIG_PPR = 800
CONFIG_PITCH = 5

colors = {
    "Blue": {"200": "#EEEEFF", "500": "#EEEEFF", "700": "#EEEEFF"},
    "BlueGray": {"200": "##005AAB", "500": "##005AAB", "700": "##005AAB"},
    "Red": {"A200": "#DDD8DD", "A500": "#DDD8DD", "A700": "#DDD8DD"},
    "Light": {"StatusBar": "#E0E0E0", "AppBar": "#202020", "Background": "#EEEEEE", "CardsDialogs": "#FFFFFF", "FlatButtonDown": "#CCCCCC"},
    "Dark": {"StatusBar": "#101010", "AppBar": "#E0E0E0", "Background": "#111111", "CardsDialogs": "#000000", "FlatButtonDown": "#333333"},
}

class ScreenSplash(MDScreen):
    def __init__(self, **kwargs):
        super(ScreenSplash, self).__init__(**kwargs)
        Logger.info("GravityMeterApp: Loading ScreenSplash")
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

class ScreenHome(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ble_client = None
        self.ble_devices = []
        self.selected_device = None
        self.scanning = False

    def detect_ble_devices(self):
        if not self.scanning:
            self.scanning = True
            threading.Thread(target=self._start_scan).start()

    def _start_scan(self):
        async def scan():
            try:
                devices = await BleakScanner.discover(timeout=10)
                self.ble_devices = [{'name': d.name or "Unknown", 'address': d.address} for d in devices]
                self.update_ble_devices_menu()
                self.show_toast(f"Found {len(self.ble_devices)} devices")
            except Exception as e:
                Logger.error(f"GravityMeterApp: Scan error: {e}")
                self.show_toast("Scan failed")
            finally:
                self.scanning = False

        asyncio.run(scan())

    @mainthread
    def update_ble_devices_menu(self):
        menu_items = [
            {
                "text": f"{d['name']} ({d['address']})",
                "viewclass": "OneLineListItem",
                "on_release": lambda x=d: self.select_ble_device(x),
            } for d in self.ble_devices
        ]
        if hasattr(self, 'menu'):
            self.menu.dismiss()
        self.menu = MDDropdownMenu(
            caller=self.ids.com_port_button,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()

    def select_ble_device(self, device):
        self.selected_device = device
        self.ids.com_port_button.text = f"{device['name']} ({device['address']})"
        if hasattr(self, 'menu'):
            self.menu.dismiss()
        self.connect_ble()

    def connect_ble(self):
        if self.selected_device:
            threading.Thread(target=self._connect_ble_device).start()

    def _connect_ble_device(self):
        async def connect():
            try:
                self.ble_client = BleakClient(self.selected_device['address'])
                await self.ble_client.connect()
                self.show_toast(f"Connected to {self.selected_device['name']}")
                Logger.info("GravityMeterApp: BLE connection successful")
            except Exception as e:
                Logger.error(f"GravityMeterApp: Connection failed: {e}")
                self.show_toast("Connection failed")

        asyncio.run(connect())

    @mainthread
    def show_toast(self, message):
        """Show a toast message."""
        toast(message)

    def open_com_port_menu(self):
        self.detect_ble_devices()
        self.show_toast("Scanning for BLE devices...")

    async def send_ble_command(self, command):
        if self.ble_client and self.ble_client.is_connected:
            try:
                await self.ble_client.write_gatt_char(BLE_CHARACTERISTIC_UUID, command.encode())
                Logger.info(f"GravityMeterApp: Sent command: {command}")
            except Exception as e:
                Logger.error(f"GravityMeterApp: Failed to send command: {e}")
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
                Logger.error("GravityMeterApp: Bluetooth is not supported on this device.")
                self.show_toast("Bluetooth is not supported on this device.")
                return None
            if not self.is_bluetooth_enabled():
                Logger.info("GravityMeterApp: Bluetooth is not enabled. Prompting user to enable it.")
                self.enable_bluetooth()
        else:
            Logger.info("GravityMeterApp: Running on non-Android platform, skipping permission requests.")

        self.theme_cls.colors = colors
        self.theme_cls.primary_palette = "BlueGray"
        self.theme_cls.accent_palette = "Blue"
        self.icon = 'assets/images/Logo_Main.png'
        # Window.size = (1366, 768)
        # Window.size = (480, 1280)
        Window.fullscreen = 'auto'
        Window.borderless = True
        Window.allow_screensaver = True
        Builder.load_file('main.kv')
        return RootScreen()

    def is_bluetooth_supported(self):
        try:
            from jnius import autoclass
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            adapter = BluetoothAdapter.getDefaultAdapter()
            return adapter is not None
        except Exception as e:
            Logger.error(f"GravityMeterApp: Error checking Bluetooth support: {e}")
            return False

    def is_bluetooth_enabled(self):
        try:
            from jnius import autoclass
            BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
            adapter = BluetoothAdapter.getDefaultAdapter()
            return adapter is not None and adapter.isEnabled()
        except Exception as e:
            Logger.error(f"GravityMeterApp: Error checking Bluetooth status: {e}")
            return False

    def enable_bluetooth(self):
        try:
            from jnius import autoclass
            Intent = autoclass('android.content.Intent')
            Settings = autoclass('android.provider.Settings')
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            intent = Intent(Settings.ACTION_BLUETOOTH_SETTINGS)
            current_activity = PythonActivity.mActivity
            current_activity.startActivity(intent)
        except Exception as e:
            Logger.error(f"GravityMeterApp: Error enabling Bluetooth: {e}")

if __name__ == '__main__':
    GravityMeterApp().run()