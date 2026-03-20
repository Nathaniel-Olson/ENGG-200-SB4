import hardware
import gc
import aioble
import bluetooth
import uasyncio as asyncio
from micropython import const

gc.collect()

# Bluetooth Setup
DEVICE_NAME = "B1_D1"
GENERIC_UUID = bluetooth.UUID(0x1D10)
ADV_INTERVAL_US = const(250_000)
BLE_AGRC = const(384) # Appearance generic remote control

connected = False
connection = None

# Service and Object Assignment
controller_service = aioble.Service(GENERIC_UUID)

left_joystick = hardware.Joystick(26, 0, 0x1D11, controller_service)
right_joystick = hardware.Joystick(28, 27, 0x1D12, controller_service)

button_1 = hardware.Button(12, 0x1D13, controller_service)
button_2 = hardware.Button(19, 0x1D14, controller_service)

green_led = hardware.LED(PinID = 1)
yellow_led = hardware.LED(PinID = 9)

aioble.register_services(controller_service)

# Async Functions
async def advertise_task():
    global connected, connection
    while True:
        connected = False
        async with await aioble.advertise(ADV_INTERVAL_US, name = DEVICE_NAME, appearance = BLE_AGRC, services = [GENERIC_UUID]) as connection:
            connected = True
            await connection.disconnected()

async def read_task():
    global connected
    while True:
        left_joystick.read()
        right_joystick.read()
        button_1.read()
        button_2.read()

        if connected:
            left_joystick.transmit(connection)
            right_joystick.transmit(connection)
            button_1.transmit(connection)
            button_2.transmit(connection)

async def led_task():
    green_led.off()
    yellow_led.off()
    toggle = True

    while True:
        if not connected:
            yellow_led.write(toggle)
            toggle = not toggle
            await asyncio.sleep_ms(250)
        if connected:
            yellow_led.off()
            green_led.on()
            await asyncio.sleep_ms(1000)

async def gc_task():
    while True:
        gc.collect()
        await asyncio.sleep_ms(5000)
            
# Main
async def main():
    await asyncio.gather(advertise_task(), read_task(), led_task(), gc_task())

try:
    asyncio.run(main())
    
except KeyboardInterrupt:
    green_led.off()
    yellow_led.off()
    print("Program Closed.")