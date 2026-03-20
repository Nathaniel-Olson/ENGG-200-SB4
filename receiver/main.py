import hardware
import gc
import aioble
import bluetooth
import uasyncio as asyncio

# Bluetooth Setup
REMOTE_NAME = "B1_D1"
GENERIC_UUID = bluetooth.UUID(0x1D10)
connected = False

# Receiver Setup
left_joystick = hardware.Receiver(0x1D11)
right_joystick = hardware.Receiver(0x1D12)
button_1 = hardware.Receiver(0x1D13)
button_2 = hardware.Receiver(0x1D14)

# Pin Assignment
green_led = hardware.LED(20)
yellow_led = hardware.LED(11)

left_motor = hardware.DCMotor(0,1,"L")
right_motor = hardware.DCMotor(3,4,"R")
servo = hardware.Servo(27)

gc.collect()

# Async Functions
async def find_remote():
    async with aioble.scan(5000, interval_us = 30000, window_us = 30000, active = True
                           ) as scanner:
        async for result in scanner:
            if result.name() == REMOTE_NAME:
                return result.device
    return None

async def connect_task():
    global connected
    while True:
        device = await find_remote()
        print("connecting...")
        if not device:
            await asyncio.sleep(1)
            continue
        try:
            connection = await device.connect()
            print("connected")
        except asyncio.TimeoutError:
            continue

        async with connection:
            connected = True
            
            service = await connection.service(GENERIC_UUID)
            
            await left_joystick.find_char_and_subscribe(service)
            await right_joystick.find_char_and_subscribe(service)
            await button_1.find_char_and_subscribe(service)
            await button_2.find_char_and_subscribe(service)

            while True:
                await asyncio.gather(
                    left_joystick.listen_and_relay_servo(servo),
                    right_joystick.listen_and_relay_motors(left_motor, right_motor),
                    button_1.listen_and_relay_led(green_led)
                    )
                
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

async def main():
    await asyncio.gather(connect_task(), led_task(), gc_task())

try:
    asyncio.run(main())
    
except KeyboardInterrupt:
    green_led.off()
    yellow_led.off()
    print("progam closed.")

