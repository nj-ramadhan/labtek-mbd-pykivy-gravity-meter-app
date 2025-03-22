import platform
from jnius import autoclass
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivymd.toast import toast
from kivy.clock import Clock, mainthread
from kivy.properties import ObjectProperty
from kivy.logger import Logger
import asyncio
import time
from bleak import BleakClient, BleakScanner
import threading


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
    screen_manager = ObjectProperty(None)
    app_window = ObjectProperty(None)

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
            time.sleep(0.5)
            self.screen_manager.current = 'screen_home'
            return False

class ScreenHome(MDScreen):
    screen_manager = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ScreenHome, self).__init__(**kwargs)
        self.ble_client = None
        self.ble_devices = []
        self.selected_device = None

    def detect_ble_devices(self):
        threading.Thread(target=self._detect_ble_devices).start()

    def _detect_ble_devices(self):
        async def scan():
            try:
                self.ble_devices = await BleakScanner.discover()
                print(f"Found BLE devices: {self.ble_devices}")
                Logger.info(f"Found BLE devices: {self.ble_devices}")
                self.update_ble_devices_menu()
                self.show_toast(f"Found {len(self.ble_devices)} BLE devices")
            except Exception as e:
                print(f"Failed to scan for BLE devices: {e}")
                Logger.error(f"Failed to scan for BLE devices: {e}")
                self.show_toast("Failed to scan for BLE devices")
        asyncio.run(scan())

    @mainthread
    def update_ble_devices_menu(self):
        # Create a dropdown menu for BLE devices
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
        toast(message)

    def open_com_port_menu(self):
        # Detect BLE devices before opening the menu
        self.detect_ble_devices()
        self.show_toast("Scanning for BLE devices...")

    def select_ble_device(self, device):
        # Set the selected BLE device
        self.selected_device = device
        self.ids.com_port_button.text = device.name if device.name else device.address
        self.menu.dismiss()
        self.connect_ble()

    def connect_ble(self):
        if self.selected_device:
            threading.Thread(target=self._connect_ble).start()

    def _connect_ble(self):
        async def connect():
            self.ble_client = BleakClient(self.selected_device)
            try:
                await self.ble_client.connect()
                print(f"Connected to {self.selected_device.name}!")
                Logger.info(f"Connected to {self.selected_device.name}!")
                self.show_toast(f"Connected to {self.selected_device.name}")
            except Exception as e:
                print(f"Failed to connect to {self.selected_device.name}: {e}")
                Logger.error(f"Failed to connect to {self.selected_device.name}: {e}")
                self.show_toast(f"Failed to connect to {self.selected_device.name}")
        asyncio.run(connect())

    async def send_ble_command(self, command):
        if self.ble_client and self.ble_client.is_connected:
            try:
                await self.ble_client.write_gatt_char(BLE_CHARACTERISTIC_UUID, command.encode())
                print(f"Sent command: {command}")
                Logger.info(f"Sent command: {command}")
                # self.show_toast(f"Sent command: {command}")
            except Exception as e:
                print(f"Failed to send command: {e}")
                Logger.error(f"Failed to send command: {e}")
                self.show_toast("Failed to send command")

    def act_home(self):
        if self.ble_client:
            asyncio.run(self.send_ble_command("HOME\n"))
            self.show_toast("Mulai Pergerakan ke posisi Awal")

    def act_up(self):
        if self.ble_client:
            asyncio.run(self.send_ble_command("UP\n"))
            self.show_toast("Mulai Pergerakan Naik Manual")

    def act_down(self):
        if self.ble_client:
            asyncio.run(self.send_ble_command("DN\n"))
            self.show_toast("Mulai Pergerakan Turun Manual")

    def act_stop(self):
        pass

    def act_start(self):
        if self.ble_client:
            set_point_pos = self.ids.tx_field.text
            set_point_pulse = int(float(set_point_pos) * CONFIG_PPR / CONFIG_PITCH)
            if set_point_pulse > 0:
                asyncio.run(self.send_ble_command(f"{set_point_pulse}\n"))
                self.show_toast(f"Mulai Pergerakan ke posisi {set_point_pos} mm")

class RootScreen(ScreenManager):
    pass

class GravityMeterApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self):
        if platform.system() == "Linux" and platform.release() == "Android":
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.BLUETOOTH,
                Permission.BLUETOOTH_ADMIN,
                Permission.BLUETOOTH_CONNECT,
                Permission.BLUETOOTH_SCAN,
                Permission.ACCESS_FINE_LOCATION
            ])        
            # Check if Bluetooth is supported and enabled
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
        Window.fullscreen = 'auto'
        Window.borderless = True
        Window.allow_screensaver = True

        Builder.load_file('main.kv')
        return RootScreen()

    def is_bluetooth_supported(self):
        """Check if the device supports Bluetooth."""
        BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
        adapter = BluetoothAdapter.getDefaultAdapter()
        return adapter is not None

    def is_bluetooth_enabled(self):
        """Check if Bluetooth is enabled on the device."""
        BluetoothAdapter = autoclass('android.bluetooth.BluetoothAdapter')
        adapter = BluetoothAdapter.getDefaultAdapter()
        return adapter is not None and adapter.isEnabled()

    def enable_bluetooth(self):
        """Prompt the user to enable Bluetooth."""
        Intent = autoclass('android.content.Intent')
        Settings = autoclass('android.provider.Settings')
        PythonActivity = autoclass('org.kivy.android.PythonActivity')

        intent = Intent(Settings.ACTION_BLUETOOTH_SETTINGS)
        current_activity = PythonActivity.mActivity
        current_activity.startActivity(intent)


if __name__ == '__main__':
    GravityMeterApp().run()