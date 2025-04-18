from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivymd.toast import toast
from kivy.clock import Clock
from kivy.properties import ObjectProperty
import time, serial, serial.tools.list_ports

colors = {
    "Blue": {"200": "#EEEEFF","500": "#EEEEFF","700": "#EEEEFF",},
    "BlueGray": {"200": "##005AAB","500": "##005AAB","700": "##005AAB",},
    "Red": {"A200": "#DDD8DD","A500": "#DDD8DD","A700": "#DDD8DD",},
    "Light": {"StatusBar": "#E0E0E0","AppBar": "#202020","Background": "#EEEEEE","CardsDialogs": "#FFFFFF","FlatButtonDown": "#CCCCCC",},
    "Dark": {"StatusBar": "#101010","AppBar": "#E0E0E0","Background": "#111111","CardsDialogs": "#000000","FlatButtonDown": "#333333",},
}

DEBUG = True
CONFIG_PPR = 800
CONFIG_PITCH = 5

class ScreenSplash(MDScreen):
    screen_manager = ObjectProperty(None)
    app_window = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ScreenSplash, self).__init__(**kwargs)
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
        # Clock.schedule_interval(self.regular_check, 3)
        self.serial_connection = None
        self.com_ports = []
        self.selected_com_port = None
        self.detect_com_ports()

    def detect_com_ports(self):
        # Get a list of available COM ports
        self.com_ports = [port.device for port in serial.tools.list_ports.comports()]
        print(f"Available COM ports: {self.com_ports}")
        
    # def regular_check(self, *args):
    #     data = ser.readline().decode().strip()
    #     print(data)

    def open_com_port_menu(self):
        # Create a dropdown menu for COM ports
        menu_items = [
            {
                "text": port,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=port: self.select_com_port(x),
            }
            for port in self.com_ports
        ]
        self.menu = MDDropdownMenu(
            caller=self.ids.com_port_button,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()

    def select_com_port(self, port):
        # Set the selected COM port
        self.selected_com_port = port
        self.ids.com_port_button.text = port
        self.menu.dismiss()
        self.connect_serial()

    def connect_serial(self):
        if self.selected_com_port:
            try:
                self.serial_connection = serial.Serial(self.selected_com_port, 9600, timeout=1)
                print(f"Connected to {self.selected_com_port}!")
            except Exception as e:
                print(f"Failed to connect to {self.selected_com_port}: {e}")

    def act_home(self):
        if self.serial_connection:
            self.serial_connection.write("HOME\n".encode())
            print("Sent home command.")        
            toast(f"Mulai Pergerakan ke posisi Awal")

    def act_up(self):
        if self.serial_connection:
            self.serial_connection.write("UP\n".encode())
            print("Sent up command.")        
            toast(f"Mulai Pergerakan Naik Manual")

    def act_down(self):
        if self.serial_connection:
            self.serial_connection.write("DN\n".encode())
            print("Sent down command.")        
            toast(f"Mulai Pergerakan Turun Manual")

    def act_stop(self):
        pass

    def act_start(self):
        if self.serial_connection:
            set_point_pos = self.ids.tx_field.text
            set_point_pulse = int(float(set_point_pos) * CONFIG_PPR / CONFIG_PITCH)
            if set_point_pulse > 0:
                self.serial_connection.write(f"{set_point_pulse}\n".encode())
                print(f"Sent position: {set_point_pos}")
                toast(f"Mulai Pergerakan ke posisi {set_point_pos} mm")

class RootScreen(ScreenManager):
    pass    

class GravityMeterApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self):
        self.theme_cls.colors = colors
        self.theme_cls.primary_palette = "BlueGray"
        self.theme_cls.accent_palette = "Blue"
        self.icon = 'asset/Logo_Main.png'
        Window.fullscreen = 'auto'
        Window.borderless = True
        # Window.size = 1080, 600
        Window.allow_screensaver = True

        Builder.load_file('main.kv')
        return RootScreen()


if __name__ == '__main__':
    GravityMeterApp().run()
