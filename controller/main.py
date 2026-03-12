import hardware

import aioble
import bluetooth
import uasyncio as asyncio
from micropython import const

# ==========================
# BLUETOOTH SETUP
# ==========================

DEVICE_NAME = "B1_D1"
GENERIC_UUID = bluetooth.UUID(0x1D10)
ADV_INTERVAL_US = const(250_000)
BLE_AGRC = const(384) # Appearance generic remote control

connected = False
connection = None

# ==========================
# SERVICE & OBJECT ASSIGNMENT
# ==========================

controller_service = aioble.Service(GENERIC_UUID)

left_joystick = hardware.Joystick(28, 0, 0x1D11, controller_service)
right_joystick = hardware.Joystick(27, 26, 0x1D12, controller_service)

button_1 = hardware.Button(18, 0x1D13, controller_service)
button_2 = hardware.Button(13, 0x1D14, controller_service)

led = hardware.LED(PinID = 1)
led.on()

aioble.register_services(controller_service)

# ==========================
# ASYNC FUNCTIONS
# ==========================

async def advertise_task():
    global connected, connection
    while True:
        connected = False
        async with await aioble.advertise(ADV_INTERVAL_US, name = DEVICE_NAME, appearance = BLE_AGRC, services = [GENERIC_UUID]) as connection:
            connected = True
            await connected.disconnected()

async def read_task():
    global connected
    while True:
        left_joystick.read()
        right_joystick.read()
        button_1.read()
        button_2.read()

        if connected:
            left_joystick.transmit()
            right_joystick.transmit()
            button_1.transmit()
            button_2.transmit()
        
        await asyncio.sleep_ms(50)

async def led_task():
    toggle = True
    while True:
        led.write(toggle)
        toggle = not toggle
        await asyncio.sleep_ms(1000 if connected else 250)

# ==========================
# MAIN
# ==========================

async def main():
    await asyncio.gather(advertise_task(), read_task(), led_task())

try:
    asyncio.run(main())
    
except KeyboardInterrupt:
    led.off()
    print("Program Closed.")

