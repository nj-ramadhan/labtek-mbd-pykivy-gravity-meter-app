import numpy as np
from kivymd.app import MDApp
from kivymd.toast import toast
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.relativelayout import MDRelativeLayout
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.config import Config
from kivy.metrics import dp
from datetime import datetime
from pathlib import Path
from kivy.properties import ObjectProperty
from kivy.properties import StringProperty
import playsound
import minimalmodbus
import time
import qrcode
import requests
import logging
import logging

from gpiozero import DigitalInputDevice
from gpiozero import Motor
from gpiozero import DigitalOutputDevice
from gpiozero import AngularServo

qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_L,
    box_size=10,
    border=4,
)

colors = {
    "Blue": {"200": "#A3D8DD","500": "#A3D8DD","700": "#A3D8DD",},
    "BlueGray": {"200": "#09343C","500": "#09343C","700": "#09343C",},
    "Red": {"A200": "#DDD8DD","A500": "#DDD8DD","A700": "#DDD8DD",},
    "Light": {"StatusBar": "#E0E0E0","AppBar": "#202020","Background": "#EEEEEE","CardsDialogs": "#FFFFFF","FlatButtonDown": "#CCCCCC",},
    "Dark": {"StatusBar": "#101010","AppBar": "#E0E0E0","Background": "#111111","CardsDialogs": "#000000","FlatButtonDown": "#333333",},
}

DEBUG = False
PASSWORD = "KYP001"
SERVER = 'https://app.kickyourplast.com/api/'
MACHINE_CODE = 'KYP001'

# modbus rtu communication paramater setup
BAUDRATE = 9600
BYTESIZES = 8
STOPBITS = 1
TIMEOUT = 0.5
PARITY = minimalmodbus.serial.PARITY_NONE
MODE = minimalmodbus.MODE_RTU

LOW_LOW_LEVEL = 25.0
LOW_LEVEL = 30.0
HIGH_LEVEL = 60.0
HIGH_HIGH_LEVEL = 65.0

DELAY_BEFORE_AUTO_DOWN = 50
DELAY_WHILE_AUTO_DOWN = 50

text_coupon = ""
flag_maintenance = False
valve_cold = False
valve_normal = False
pump_main = False
pump_cold = False
pump_normal = False
linear_motor = False
servo_open = False
main_switch = False

#spec -> 400 pulse per liter
pulsePerLiter = 155
pulsePerMiliLiter = pulsePerLiter/1000

cold = False
product = 0
idProduct = 0
productPrice = 0
pulse = 0
levelMainTank = 50.0
levelMainTankArray = []
windowSize = 200
levelNormalTank = 0.0
levelColdTank = 0.0
maxMainTank = 8000.0
maxNormalTank = 350.0
maxColdTank = 250.0
qrSource = 'asset/qr_payment.png'
payment_check = None

fill_state = False
fill_previous = False
count_time_initiate = 0

if(not DEBUG):
    # input declaration 
    in_machine_ready = DigitalInputDevice(24, pull_up=None, active_state=True, bounce_time=4)
    in_sensor_proximity_bawah = DigitalInputDevice(23, pull_up=None, active_state=False, bounce_time=.01) #pull_up=false mean pull_down
    in_sensor_proximity_atas = DigitalInputDevice(22, pull_up=None, active_state=False, bounce_time=.01)
    in_sensor_flow = DigitalInputDevice(27, pull_up=None, active_state=False, bounce_time=.0001)

    # output declaration 
    out_valve_cold = DigitalOutputDevice(26)
    out_valve_normal = DigitalOutputDevice(20)
    out_pump_main = DigitalOutputDevice(21)
    out_pump_cold = DigitalOutputDevice(5)
    out_pump_normal = DigitalOutputDevice(6)
    out_servo = AngularServo(12, initial_angle=0, min_angle=-90, max_angle=90, max_pulse_width=2.5/1000, min_pulse_width=1/1000)
    out_motor_linear = Motor(9, 16)
    out_valve_cold.on() # on = open 
    out_valve_normal.on() # on = open
    out_pump_main.on()
    out_pump_cold.off()
    out_pump_normal.off()
    out_motor_linear.stop()
               
    time.sleep(0.5)

    # modbus communication of sensor declaration 
    mainTank = minimalmodbus.Instrument('/dev/ttyUSB0', 1)
    mainTank.serial.baudrate = BAUDRATE
    mainTank.serial.bytesize = BYTESIZES
    mainTank.serial.parity = PARITY
    mainTank.serial.stopbits = STOPBITS
    mainTank.serial.timeout = 0.5
    mainTank.mode = MODE
    mainTank.clear_buffers_before_each_transaction = True

    coldTank = minimalmodbus.Instrument('/dev/ttyUSB0', 2)
    coldTank.serial.baudrate = BAUDRATE
    coldTank.serial.bytesize = BYTESIZES
    coldTank.serial.parity = PARITY
    coldTank.serial.stopbits = STOPBITS
    coldTank.serial.timeout = 0.5
    coldTank.mode = MODE
    coldTank.clear_buffers_before_each_transaction = True

    normalTank = minimalmodbus.Instrument('/dev/ttyUSB0', 3)
    normalTank.serial.baudrate = BAUDRATE
    normalTank.serial.bytesize = BYTESIZES
    normalTank.serial.parity = PARITY
    normalTank.serial.stopbits = STOPBITS
    normalTank.serial.timeout = 0.5
    normalTank.mode = MODE
    normalTank.clear_buffers_before_each_transaction = True

def speak(text, name):
    try:
        # tts = gTTS(text=text, lang='id', slow=False)
        filename = "asset/sound/"+ name + '.mp3'
        # tts.save(filename)
        # playsound.playsound(filename, False)
    except Exception as e:
        print("error play sound file", e)

def machine_ready():
    global main_switch

    main_switch = in_machine_ready.value
    print(f'main switch condition: {main_switch}')

    if(main_switch):
        try :
            requests.patch(SERVER + 'machines/' + MACHINE_CODE, data={
                'status' : 'ready'
            })
        except Exception as e:
            print(e)
    else:
        try :
            requests.patch(SERVER + 'machines/' + MACHINE_CODE, data={
                'status' : 'not_ready'
            })
        except Exception as e:
            print(e)
        
def count_pulse():
    global pulse

    pulse += 1
    print(f'pulse count: {pulse}')

if (not DEBUG) : in_machine_ready.when_activated = machine_ready
if (not DEBUG) : in_sensor_flow.when_activated = count_pulse 

class ScreenSplash(MDScreen):
    screen_manager = ObjectProperty(None)
    app_window = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ScreenSplash, self).__init__(**kwargs)
        Clock.schedule_interval(self.update_progress_bar, .01)
        Clock.schedule_interval(self.retry_get_products, 60)
        Clock.schedule_interval(self.retry_update_status, 3600)
        Clock.schedule_interval(self.regular_check, 1)
#         Clock.schedule_interval(self.main_tank_read, 1)

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
            self.screen_manager.current = 'screen_standby'
            return False

    def main_tank_read(self, *args):
        global levelMainTank, levelMainTankArray, maxMainTank

    def regular_check(self, *args):
        global levelColdTank, levelMainTank, levelMainTankArray, levelNormalTank, maxColdTank, maxMainTank, maxNormalTank, out_pump_main, out_valve_cold, out_valve_normal, in_machine_ready
        global flag_maintenance
        global main_switch

        if(not DEBUG) :
            try:
                main_switch = in_machine_ready.value

                if(not flag_maintenance):
                    if(levelColdTank <= LOW_LOW_LEVEL):
                        out_pump_main.off() # turn on main pump
                        out_valve_cold.on() # open cold water valve
                        
                    if(levelNormalTank <= LOW_LOW_LEVEL):
                        out_pump_main.off() # turn on main pump
                        out_valve_normal.on() # open normal water valve

                    if(levelColdTank >= HIGH_HIGH_LEVEL):
                        out_valve_cold.off() # close cold water valve

                    if(levelNormalTank >= HIGH_HIGH_LEVEL):
                        out_valve_normal.off() # close normal water valve

                    if(levelNormalTank >= HIGH_LEVEL and levelColdTank >= HIGH_LEVEL):
                        out_pump_main.on() # turn off main pump

            except Exception as e:
                print(f'Error automate pump: {e}')
        # program for reading sensor end control system algorithm
            try:
                read = mainTank.read_register(0x0101,0,3,False)
                levelMainTank = round(100 - (read * 100 / maxMainTank),2)
                time.sleep(.1)
            except Exception as e:
                print(f'Error reading level sensor main tank: {e}')
                
            try:
                read = coldTank.read_register(0x0101,0,3,False)
                levelColdTank = round(100 - (read * 100 / maxColdTank),2)                
                time.sleep(.1)
            except Exception as e:
                print(f'Error reading level sensor cold tank: {e}')

            try:
                read = normalTank.read_register(0x0101,0,3,False)
                levelNormalTank = round(100 - (read * 100 / maxNormalTank),2)    
                time.sleep(.1)
            except Exception as e:
                print(f'Error reading level sensor normal tank: {e}')
        else:
            main_switch = True

    def retry_get_products(self, *args):   
        try :
            screen_choose_product = self.screen_manager.get_screen('screen_choose_product')
            screen_choose_product.reload_products()
            print("try reloading products")

        except Exception as e:                    
            print(f'Error reload products:{e}')

    def retry_update_status(self, *args):   
        global main_switch

        if(not flag_maintenance):
            if(main_switch):
                if(levelMainTank <= LOW_LEVEL):
                    try :
                        requests.patch(SERVER + 'machines/' + MACHINE_CODE, data={
                            'stock' : str(levelMainTank),
                            'status' : 'low_level'
                        })
                    except Exception as e:
                        print(e)
                    print('updating status to server')

                    if (levelMainTank <= LOW_LOW_LEVEL):
                        try :
                            requests.patch(SERVER + 'machines/' + MACHINE_CODE, data={
                                'stock' : str(levelMainTank),
                                'status' : 'not_ready'
                            })
                        except Exception as e:
                            print(e)

                        self.screen_manager.current = 'screen_standby'
                    else:
                        if (self.screen_manager.current == 'screen_standby') : self.screen_manager.current = 'screen_choose_product'
                else:
                    requests.patch(SERVER + 'machines/' + MACHINE_CODE, data={
                        'stock' : str(levelMainTank),
                        'status' : 'ready'
                    })
            else:
                try :
                    requests.patch(SERVER + 'machines/' + MACHINE_CODE, data={
                        'status' : 'not_ready'
                    })
                except Exception as e:
                    print(e)
                    

class ScreenStandby(MDScreen):
    screen_manager = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ScreenStandby, self).__init__(**kwargs)
        Clock.schedule_interval(self.regular_check, 3)

    def regular_check(self, *args):
        global main_switch

        if(not DEBUG) :
            try:
                main_switch = in_machine_ready.value        
            except Exception as e:                    
                print(f'Error standby check:{e}')
        else:
            main_switch = True

                # program for displaying IO condition
        if (main_switch):
            if (self.screen_manager.current == 'screen_standby'):
                self.screen_manager.current = 'screen_choose_product'
                Clock.unschedule(self.regular_check)

        else:
            # print("machine is standby")
            if (self.screen_manager.current == 'screen_choose_product'):
                self.screen_manager.current == 'screen_standby'

class ScreenChooseProduct(MDScreen):
    screen_manager = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ScreenChooseProduct, self).__init__(**kwargs)
        Clock.schedule_interval(self.regular_check, 0.5)
        Clock.schedule_once(self.delayed_init, 5)

    def delayed_init(self, *args):
        self.reload_products()

    def reload_products(self):
        try :
            r = requests.get(SERVER + 'products', {"is_featured" : "1"})
            products = r.json()['data']            
            
            layout_products = self.ids.layout_products
            layout_products.clear_widgets(children=None)

        except Exception as e:
            toast("Error request product data")
            print(e)

        try:
            layout_products = self.ids.layout_products
            for p in products :
                layout_products.add_widget(
                    MDCard(
                        MDRelativeLayout(
                            Image(
                                # source = 'asset/' + str(p['size_in_ml'])+'ml.png',
                                source = 'asset/350ml.png',
                                pos_hint = {"center_x": .5, "center_y": .5},
                                allow_stretch = True
                            ),
                            MDLabel(
                                text = str(p['size_in_ml'])+'ml',
                                adaptive_size= True,
                                pos= ["12dp", "28dp"],
                                bold= True
                            ),
                            MDLabel(
                                text = 'Rp. '+str(p['price']),
                                adaptive_size= True,
                                pos= ["12dp", "12dp"],
                                # bold= True
                            )
                        ),
                        id = str(p['id']),
                        ripple_behavior = True,
                        on_press = lambda a, x = p['size_in_ml'], y = p['id'], z = p['price'] : self.choose_payment(x,y,z)
                    )
                )
        except Exception as e:
            toast_msg = f'Error Reload Products: {e}'
            print(toast_msg)

    def screen_scan_qr(self):
        self.screen_manager.current = 'screen_scan_qr'
            
    def cold_mode(self, value):
        global cold
        cold = value
        
    def choose_payment(self, size, id, price):
        global product, idProduct, productPrice
        self.screen_manager.current = 'screen_choose_payment'
        product = size
        idProduct = id
        productPrice = price
        toast("Choose your payment method")
        # print(idProduct,type(idProduct))
        # print(product,type(product))
        # print(productPrice,type(productPrice))

    def screen_info(self):
        self.screen_manager.current = 'screen_info'

    def regular_check(self, *args):
        # program for displaying IO condition
        if (cold):
            self.ids.bt_cold.md_bg_color = "#3C9999"
            self.ids.bt_normal.md_bg_color = "#09343C"
        else:
            self.ids.bt_cold.md_bg_color = "#09343C"
            self.ids.bt_normal.md_bg_color = "#3C9999"       

class ScreenScanQr(MDScreen):
    screen_manager = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ScreenScanQr, self).__init__(**kwargs)
        Clock.schedule_interval(self.refocusing, 2)

    def on_enter(self):
        Clock.schedule_once(self.text_refocus, 0.5)

    def text_refocus(self, dt):
        self.ids.coupon.focus = True

    def coupon_validate(self):
        global text_coupon, cold, product
        
        text_coupon = self.ids.coupon.text
        message = "Error connection"
#         text_coupon = text_coupon.upper()
        print(text_coupon)
#         if (text_coupon != ""):
        try :
            r = requests.post(SERVER + 'transactions/' + text_coupon + '/used_machine', data={'machine_code' : MACHINE_CODE})

            status = r.json()['status']
            message = r.json()['message']

            if (status == "success"):
                endpoint = f'{SERVER}transaction_by_code/{text_coupon}'
                print(endpoint)

                r = requests.get(endpoint.strip())

                cold = False if (r.json()['transaction_details'][0]['drink_type']=='regular') else True
                product = r.json()['transaction_details'][0]['size']
                toast("Success! Fit your tumbler then press Start")
                self.screen_manager.current = 'screen_operate'

            else:
                toast(f'Coupon {text_coupon}, {message}')
        except Exception as e:
            toast(f'Coupon {text_coupon}, {message}')
            
        text_coupon = ""
        self.ids.coupon.text = ""

    def refocusing(self, *args):
        if(self.screen_manager.current == 'screen_scan_qr'):
            if (self.ids.coupon.focus == False):
                self.ids.coupon.focus = True

    def screen_choose_product(self):
        self.screen_manager.current = 'screen_choose_product'

class ScreenChoosePayment(MDScreen):
    screen_manager = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ScreenChoosePayment, self).__init__(**kwargs)

    def pay(self, method):
        global qr, qrSource, product, idProduct, cold, productPrice, payment_check

        print(method)
        if(method=="GOPAY"):
            # ..... create transaction
            qrSource = self.create_transaction(
                machine_code=MACHINE_CODE,
                method='gopay',
                product_id=idProduct,
                product_size=product,
                qty=1,
                price=productPrice,
                product_type="cold" if (cold) else "normal",
                # phone=self.phone
            )

            f = open('asset/qr_payment.png', 'wb')
            f.write(requests.get(qrSource).content)
            f.close

            self.screen_manager.current = 'screen_qr_payment'
            # print("payment qris")

            # .... scheduling payment check
            self.n_payment_check = 0
            toast("Please pay, and wait for us to verify")
            payment_check = Clock.schedule_interval(self.payment_check, 2)
            speak("pembayaran melalui gopay dipilih, silahkan scan kode QR yang tampil dilayar pada aplikasi gojek Anda", "pay_gopay")

        elif(method=="QRIS"):
            # ..... create transaction
            qrSource = self.create_transaction(
                machine_code=MACHINE_CODE,
                method='qris',
                product_id=idProduct,
                product_size=product,
                qty=1,
                price=productPrice,
                product_type="cold" if (cold) else "normal",
                # phone=self.phone
            )
                
            f = open('asset/qr_payment.png', 'wb')
            f.write(requests.get(qrSource).content)
            f.close

            self.screen_manager.current = 'screen_qr_payment'
            
            self.n_payment_check = 0
            toast("Please pay, and wait for us to verify")
            payment_check = Clock.schedule_interval(self.payment_check, 2)
            speak("Silahkan lakukan pembayaran dengan menggunakan kode QR yang ada pada layar", "pay_qris")

    def create_transaction(self, method, machine_code, product_id, product_size, qty, price, product_type, phone='-'):
        try :
            r = requests.post(SERVER + 'machine_transactions', json={
                "payment_method": method,
                "machine_code": machine_code,
                "phone": phone,
                "items": [
                    {
                        "product_id": product_id,
                        "qty": qty,
                        "size": product_size,
                        "unit_price": price,
                        "drink_type": product_type
                    }
                ]
            })
            # print(r.json()['data'])
            self.transaction_id = r.json()['data']['id']
            print("transaction id : ", self.transaction_id)
            return r.json()['data']['payment_response_parameter']['qr_string'] if (method == 'qris') else r.json()['data']['payment_response_parameter']['actions'][0]['url']
        except Exception as e:
            print(e)
            toast("payment error")
    
    def payment_check(self, *args):
        self.n_payment_check += 1
        print(self.n_payment_check)
        if (self.n_payment_check <= 60):
            try :
                r = requests.get(SERVER + 'machine_transactions/' + str(self.transaction_id))

                print(r.json()['payment_status'])
                
                if (r.json()['payment_status'] == 'settlement'):
                    Clock.unschedule(self.payment_check)
                    # toast('payment success')
                    self.screen_manager.current = 'screen_operate'
                    toast("Success! Fit your tumbler then press Start")
                    speak("Terima kasih, pembayaran berhasil diterima", "pay_succes")
                    time.sleep(0.5)
                    speak("silahkan atur ketinggian tumbler Anda dengan menekan tombol up dan down pada layar", "command_tumbler")
                    time.sleep(0.5)
                    speak("tekan tombol start untuk mulai pengisian air, dan tombol stop untuk berhenti", "command_fill")
                    self.transaction_id = ''

                # elif (r.json()['payment_status'] != 'pending'):
                #     Clock.unschedule(self.payment_check)
                #     toast("Pembayaran gagal, silahkan coba lagi")
                #     speak("Maaf, pembayaran gagal, silahkan coba kembali", "pay_failed")
                #     self.screen_manager.current = 'screen_choose_product'
                #     print(r.json()['data']['payment_status'])
                #     self.transaction_id = ''

                    
            except Exception as e:
                # self.transaction_id = ''
                print(e)
            
        else:
            Clock.unschedule(self.payment_check)
            toast("Payment failed, please try again")
            speak("Maaf, pembayaran gagal, silahkan coba kembali", "pay_failed")
            self.transaction_id = ''
            self.screen_manager.current = 'screen_choose_product'

    def screen_choose_product(self):
        self.screen_manager.current = 'screen_choose_product'
        Clock.unschedule(self.payment_check)


class ScreenOperate(MDScreen):
    screen_manager = ObjectProperty(None)

    def __init__(self, **kwargs):       
        super(ScreenOperate, self).__init__(**kwargs)
        Clock.schedule_interval(self.regular_check, .1)

    def act_up(self):
        global linear_motor, out_motor_linear

        self.ids.bt_up.md_bg_color = "#3C9999"
        if (not DEBUG) : out_motor_linear.forward()
        # toast("tumbler base is going up")

    def act_down(self):
        global linear_motor, out_motor_linear

        self.ids.bt_down.md_bg_color = "#3C9999"
        if (not DEBUG) : out_motor_linear.backward()
        # toast("tumbler base is going down")

    def act_stop(self):
        global linear_motor, out_motor_linear

        self.ids.bt_up.md_bg_color = "#09343C"
        self.ids.bt_down.md_bg_color = "#09343C"
        if (not DEBUG) : out_motor_linear.stop()

    def fill_start(self):
        global pulse, fill_state

        if (not DEBUG and not fill_state) :
            pulse = 0 
            fill_state = True

        print("fill start")
        toast("water filling is started")
        speak("pengisian air dimulai, mohon tekan tombol stop apabila botol Anda telah penuh", "fill_start")

    def fill_stop(self):
        global out_pump_cold, out_pump_normal, servo_open, fill_state
        global levelMainTank

        servo_open = False
        fill_state = False

        if (not DEBUG) :
            out_pump_cold.off()
            out_pump_normal.off()
            time.sleep(.5)
            out_servo.angle = 0
            levelMainTank -= 2

        print("fill stop")
        toast("thank you for decreasing plastic bottle trash by buying our product")
        speak("terimakasih telah mengurangi sampah botol plastik dengan membeli produk kami", "fill_stop")
        self.screen_manager.current = 'screen_choose_product'

    def regular_check(self, *args):
        global pulse, product, pulsePerMiliLiter, in_sensor_proximity_atas, in_sensor_proximity_bawah, out_pump_cold, out_pump_normal, out_servo, servo_open
        global fill_state, fill_previous, count_time_initiate

        if (fill_state):
            count_time_initiate = DELAY_BEFORE_AUTO_DOWN
            fill_previous = True

            if (pulse <= pulsePerMiliLiter * product):
             #   if (in_sensor_proximity_atas.value or in_sensor_proximity_bawah.value):
                if (True):        
                    out_servo.angle = 90
                    servo_open = True
                    time.sleep(.5)
                    out_pump_cold.on() if (cold) else out_pump_normal.on()
                else :
                    out_servo.angle = 0
                    out_pump_cold.off()
                    out_pump_normal.off()
                    time.sleep(.5)
                    servo_open = False
                    toast("please put your tumbler")
                    speak("mohon letakkan tumbler Anda", "put_tumbler")

            else :
                self.fill_stop()
        
        elif(not fill_state and fill_previous):
            #print(count_time_initiate)
            if (count_time_initiate == 0):
                fill_previous = False

            if (count_time_initiate > 0):
                count_time_initiate -= 1

            if (count_time_initiate <= DELAY_WHILE_AUTO_DOWN):
                self.act_down()

class ScreenQRPayment(MDScreen):
    screen_manager = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ScreenQRPayment, self).__init__(**kwargs)
        Clock.schedule_interval(self.regular_check, 10)
        
    def regular_check(self, *args):
        self.ids.image_qr_payment.source = 'asset/qr_payment.png'
        self.ids.image_qr_payment.reload()

    def cancel(self):
        global payment_check
        Clock.unschedule(payment_check)
        self.screen_manager.current = 'screen_choose_product'

    def dummy_success(self):
        global payment_check
        Clock.unschedule(payment_check)
        toast("Success! Fit your tumbler then press Start")
        self.screen_manager.current = 'screen_operate' 

class ScreenInfo(MDScreen):
    screen_manager = ObjectProperty(None)
    password = ""

    def __init__(self, **kwargs):
        super(ScreenInfo, self).__init__(**kwargs)

    def screen_choose_product(self):
        self.ids.textfield_password.opacity = 0.0
        self.ids.textfield_password.text = ""
        self.screen_manager.current = 'screen_choose_product'

    def screen_maintenance(self):
        self.ids.textfield_password.opacity = 0.0
        self.ids.textfield_password.text = ""
        self.screen_manager.current = 'screen_maintenance'      

    def loading_password(self):
        self.password = self.ids.textfield_password.text
        print(self.password)
        if(self.password == PASSWORD):
            self.screen_maintenance()
        else:
            toast("Password is incorrect")

    def show_password_textfield(self):
        self.ids.textfield_password.opacity = 1.0
        print("textfield is shown")

class ScreenMaintenance(MDScreen):
    screen_manager = ObjectProperty(None)

    def __init__(self, **kwargs):
        super(ScreenMaintenance, self).__init__(**kwargs)
        Clock.schedule_interval(self.regular_check, .1)
    
    def act_maintenance(self):
        global flag_maintenance

        if (flag_maintenance):
            flag_maintenance = False
            toast("Mode running")
        else:
            flag_maintenance = True
            toast("Mode maintenance")

    def act_valve_cold(self):
        global valve_cold, out_valve_cold
        if (valve_cold):
            valve_cold = False 
            if (not DEBUG) : out_valve_cold.off()
        else:
            valve_cold = True 
            if (not DEBUG) : out_valve_cold.on()

    def act_valve_normal(self):
        global valve_normal, out_valve_normal
        if (valve_normal):
            valve_normal = False 
            if (not DEBUG) : out_valve_normal.off()
        else:
            valve_normal = True 
            if (not DEBUG) : out_valve_normal.on()

    def act_pump_main(self):
        global pump_main, out_pump_main
        if (pump_main):
            pump_main = False            
            if (not DEBUG) : out_pump_main.on()
        else:
            pump_main = True
            if (not DEBUG) : out_pump_main.off()

    def act_pump_cold(self):
        global pump_cold, out_pump_cold
        if (pump_cold):
            pump_cold = False
            if (not DEBUG) : out_pump_cold.off()
        else:
            pump_cold = True 
            if (not DEBUG) : out_pump_cold.on()

    def act_pump_normal(self):
        global pump_normal, out_pump_normal
        if (pump_normal):
            pump_normal = False
            if (not DEBUG) : out_pump_normal.off()
        else:
            pump_normal = True
            if (not DEBUG) : out_pump_normal.on()

    def act_open(self):
        global servo_open, out_servo

        servo_open = True
        if (not DEBUG) : out_servo.angle = 90      

    def act_close(self):
        global servo_open, out_servo

        servo_open = False
        if (not DEBUG) : out_servo.angle = 0

    def act_up(self):
        global linear_motor, out_motor_linear

        self.ids.bt_up.md_bg_color = "#3C9999"
        if (not DEBUG) : out_motor_linear.forward()
        toast("tumbler base is going up")

    def act_down(self):
        global linear_motor, out_motor_linear

        self.ids.bt_down.md_bg_color = "#3C9999"
        if (not DEBUG) : out_motor_linear.backward()
        toast("tumbler base is going down")

    def act_stop(self):
        global linear_motor, out_motor_linear

        self.ids.bt_up.md_bg_color = "#09343C"
        self.ids.bt_down.md_bg_color = "#09343C"
        if (not DEBUG) : out_motor_linear.stop()

    def exit(self):
        self.screen_manager.current = 'screen_choose_product'

    def regular_check(self, *args):
        global levelColdTank, levelMainTank, levelNormalTank, flag_maintenance

        self.ids.lb_level_main.text = f"{levelMainTank} %"
        self.ids.lb_level_cold.text = f"{levelColdTank} %"
        self.ids.lb_level_normal.text = f"{levelNormalTank} %"

        # program for displaying IO condition        
        if (flag_maintenance): self.ids.bt_maintenance.md_bg_color = "#3C9999"
        else: self.ids.bt_maintenance.md_bg_color = "#09343C"

        if (valve_cold): self.ids.bt_valve_cold.md_bg_color = "#3C9999"
        else: self.ids.bt_valve_cold.md_bg_color = "#09343C"

        if (valve_normal): self.ids.bt_valve_normal.md_bg_color = "#3C9999"
        else: self.ids.bt_valve_normal.md_bg_color = "#09343C"

        if (pump_main): self.ids.bt_pump_main.md_bg_color = "#3C9999"
        else: self.ids.bt_pump_main.md_bg_color = "#09343C"

        if (pump_cold): self.ids.bt_pump_cold.md_bg_color = "#3C9999"
        else: self.ids.bt_pump_cold.md_bg_color = "#09343C"

        if (pump_normal): self.ids.bt_pump_normal.md_bg_color = "#3C9999"
        else: self.ids.bt_pump_normal.md_bg_color = "#09343C"

        if (servo_open):
            self.ids.bt_open.md_bg_color = "#3C9999"
            self.ids.bt_close.md_bg_color = "#09343C"
        else:
            self.ids.bt_open.md_bg_color = "#09343C"
            self.ids.bt_close.md_bg_color = "#3C9999"

class RootScreen(ScreenManager):
    pass    

class WaterDispenserMachineApp(MDApp):
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
    WaterDispenserMachineApp().run()
