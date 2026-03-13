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

button_1 = hardware.Button(17, 0x1D13, controller_service)
button_2 = hardware.Button(14, 0x1D14, controller_service)

led = hardware.LED(PinID = 1)

aioble.register_services(controller_service)

# Async Functions
async def advertise_task():
    global connected, connection
    while True:
        connected = False
        async with await aioble.advertise(ADV_INTERVAL_US, name = DEVICE_NAME, appearance = BLE_AGRC, services = [GENERIC_UUID]) as connection:
            connected = True
            await connection.disconnected()
            gc.collect()

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
        
        gc.collect()
        await asyncio.sleep_ms(50)

async def led_task():
    toggle = True
    while True:
        led.write(toggle)
        toggle = not toggle
        await asyncio.sleep_ms(1000 if connected else 250)

# Main
async def main():
    await asyncio.gather(advertise_task(), read_task(), led_task())

try:
    asyncio.run(main())
    
except KeyboardInterrupt:
    led.off()
    print("Program Closed.")

except OSError:
    led.off()
    print("failure to connect, fatal")

