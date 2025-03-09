from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.screenmanager import Screen
from kivy.clock import Clock
import serial
import serial.tools.list_ports

# KivyMD layout
KV = '''
BoxLayout:
    orientation: 'vertical'
    padding: 20
    spacing: 20

    MDLabel:
        text: "Stepper Motor Control"
        halign: "center"
        font_style: "H4"

    MDBoxLayout:
        orientation: 'horizontal'
        size_hint_y: None
        height: "48dp"
        spacing: 10

        MDLabel:
            text: "Select COM Port:"
            size_hint_x: None
            width: "120dp"

        MDRaisedButton:
            id: com_port_button
            text: "Select COM Port"
            on_release: app.open_com_port_menu()

    MDTextField:
        id: position_input
        hint_text: "Enter Desired Position"
        input_filter: "int"
        multiline: False

    MDRaisedButton:
        text: "Move Stepper"
        on_release: app.send_position()

    MDRaisedButton:
        text: "Home Stepper"
        on_release: app.send_home_command()
'''

class StepperControlApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.serial_connection = None
        self.com_ports = []
        self.selected_com_port = None

    def build(self):
        # Detect available COM ports
        self.detect_com_ports()
        return Builder.load_string(KV)

    def detect_com_ports(self):
        # Get a list of available COM ports
        self.com_ports = [port.device for port in serial.tools.list_ports.comports()]
        print(f"Available COM ports: {self.com_ports}")

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
            caller=self.root.ids.com_port_button,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()

    def select_com_port(self, port):
        # Set the selected COM port
        self.selected_com_port = port
        self.root.ids.com_port_button.text = port
        self.menu.dismiss()
        self.connect_serial()

    def connect_serial(self):
        if self.selected_com_port:
            try:
                self.serial_connection = serial.Serial(self.selected_com_port, 9600, timeout=1)
                print(f"Connected to {self.selected_com_port}!")
            except Exception as e:
                print(f"Failed to connect to {self.selected_com_port}: {e}")

    def send_position(self):
        if self.serial_connection:
            desired_position = self.root.ids.position_input.text
            if desired_position:
                self.serial_connection.write(f"{desired_position}\n".encode())
                print(f"Sent position: {desired_position}")

    def send_home_command(self):
        if self.serial_connection:
            self.serial_connection.write("HOME\n".encode())
            print("Sent home command.")

    def on_stop(self):
        if self.serial_connection:
            self.serial_connection.close()
            print("Serial connection closed.")

if __name__ == "__main__":
    StepperControlApp().run()