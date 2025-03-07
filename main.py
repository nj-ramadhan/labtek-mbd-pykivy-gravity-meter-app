from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.toast import toast
from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
import time
import requests

colors = {
    "Blue": {"200": "#EEEEFF","500": "#EEEEFF","700": "#EEEEFF",},
    "BlueGray": {"200": "##005AAB","500": "##005AAB","700": "##005AAB",},
    "Red": {"A200": "#DDD8DD","A500": "#DDD8DD","A700": "#DDD8DD",},
    "Light": {"StatusBar": "#E0E0E0","AppBar": "#202020","Background": "#EEEEEE","CardsDialogs": "#FFFFFF","FlatButtonDown": "#CCCCCC",},
    "Dark": {"StatusBar": "#101010","AppBar": "#E0E0E0","Background": "#111111","CardsDialogs": "#000000","FlatButtonDown": "#333333",},
}

DEBUG = True

# modbus rtu communication paramater setup
BAUDRATE = 9600
BYTESIZES = 8
STOPBITS = 1
TIMEOUT = 0.5

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
        Clock.schedule_interval(self.regular_check, 3)

    def regular_check(self, *args):
        global main_switch

    def act_home(self):
        toast(f"Mulai Pergerakan ke posisi Awal")

    def act_up(self):
        toast(f"Pergerakan Naik")

    def act_down(self):
        toast(f"Pergerakan Turun")

    def act_stop(self):
        pass

    def act_start(self):
        set_point = self.ids.tx_field.text
        toast(f"Mulai Pergerakan ke posisi {set_point} mm")


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
