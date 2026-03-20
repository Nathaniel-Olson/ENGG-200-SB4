import aioble
import bluetooth
from machine import ADC, Pin

# Hardware Classes
class Joystick:
    def __init__(self, xPinID: int, yPinID: int, UUID: hex, service):
        
        # Pin Assignment
        self.xPin = ADC(xPinID)
        self.yPin = ADC(yPinID)

        # Attributes
        self.x = 32767
        self.y = 32767
        
        # Bluetooth
        self.UUID = bluetooth.UUID(UUID)
        self.char = aioble.Characteristic(service, self.UUID, read = True, notify = True)
        self.msg = f"{self.x},{self.y}"

    def read(self):
        self.x = self.xPin.read_u16()
        self.y = self.yPin.read_u16()
        self.msg = f"{self.x},{self.y}"
        print(self.msg)
    
    def transmit(self, connection):
        self.char.notify(connection, self.msg.encode())
        print("notifying Joystick")


class Button:
    def __init__(self, PinID: int, UUID: hex, service):

        # Pin Assignment
        self.buttonPin = Pin(PinID, Pin.IN, Pin.PULL_UP)

        # Attributes
        self.value = 0

        # Bluetooth
        self.UUID = bluetooth.UUID(UUID)
        self.char = aioble.Characteristic(service, self.UUID, read = True, notify = True)
        self.msg = f"{self.value}"

    def read(self):
        self.value = (0 if self.buttonPin.value() else 1)
    
    def transmit(self, connection):
        self.char.notify(connection, self.msg.encode())

class LED:
    def __init__(self, PinID: int):
        self.ledPin = Pin(PinID, Pin.OUT)
        self.value = 0 # off
    
    def write(self, value: bool):
        if value == 0:
            self.ledPin.off()
        if value == 1:
            self.ledPin.on()

    def on(self):
        self.ledPin.on()
    
    def off(self):
        self.ledPin.off()
