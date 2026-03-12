import math
import bluetooth
from machine import PWM, Pin

class DCMotor:
    def __init__(self, ePinID, mPinID, direction, frequency_hz = 500, deadzone_u16 = 500, smoothing_curve = lambda i: i ** 3):
        # Pin Assignment
        self.ePin = PWM(Pin(ePinID))
        self.mPin = Pin(mPinID, Pin.OUT)

        # Attributes
        self.direction = direction
        self.dz_range = deadzone_u16
        
        # note that the smoothing curve must have a range of [0,1] on the domain [0,1]
        self.smoothing_curve = smoothing_curve

        # Other Assignments
        self.ePin.freq(frequency_hz)
    
    def write(self, joystick_input):
        # take x and y, centering at 0
        x = joystick_input[0] - 32767
        y = joystick_input[1] - 32767
        
        if abs(x) < self.dz_range:
            x = 0
        
        if abs(y) < self.dz_range:
            y = 0
        
        if x == 0:
            if y == 0:
                theta = 0
            elif y < 0:
                theta = math.pi / 2
            elif y > 0:
                theta = 3 * math.pi / 2
        elif y == 0:
            if x > 0:
                theta = 0
            if x < 0:
                theta = math.pi
        else:
            theta_r = math.atan(y/x)
            theta = theta_r * -1 + (0 if x > 0 else math.pi) + (2 * math.pi if y > 0 and x > 0 else 0)
        
        if self.direction == "R":
            trig = math.sin(theta - math.pi / 4)
        elif self.direction == "L":
            trig = math.cos(theta - math.pi / 4)
            

        
        power = abs(int(trig * 65535 * math.sqrt((x/32767)**2 + (y/32767)**2)) * math.sqrt(2))
        sign = (0 if trig > 0 else 1)
    
        print(f"{self.direction} {theta=}, {power=}")
        
        # smoothing curve
        power = int(self.smoothing_curve(power / 65535) * 65535)
        
        if power > 65535:
            power = 65535
        
        self.mPin.value(sign)
        self.ePin.duty_u16(power)
    
    def stop(self):
        self.ePin.duty_u16(0)

class Servo:
    __servo_pwm_freq = 50
    __min_u16_duty = 1640 - 2 # offset for correction
    __max_u16_duty = 7864 #+ 7864  # offset for correction
    min_angle = 0
    max_angle = 180
    current_angle = 0.001

    def __init__(self, pin):
        self.__initialise(pin)
        print("servo init")

    def update_settings(self, servo_pwm_freq, min_u16_duty, max_u16_duty, min_angle, max_angle, pin):
        self.__servo_pwm_freq = servo_pwm_freq
        self.__min_u16_duty = min_u16_duty
        self.__max_u16_duty = max_u16_duty
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.__initialise(pin)

    def move(self, angle):
        # round to 2 decimal places, so we have a chance of reducing unwanted servo adjustments
        angle = round(angle, 2)
        # do we need to move?
        if angle == self.current_angle:
            return
        self.current_angle = angle
        # calculate the new duty cycle and move the motor
        duty_u16 = self.__angle_to_u16_duty(angle)
        self.__motor.duty_u16(duty_u16)

    def __angle_to_u16_duty(self, angle):
        return int((angle - self.min_angle) * self.__angle_conversion_factor) + self.__min_u16_duty

    def __initialise(self, pin):
        self.current_angle = -0.001
        self.__angle_conversion_factor = (self.__max_u16_duty - self.__min_u16_duty) / (self.max_angle - self.min_angle)
        self.__motor = PWM(Pin(pin))
        self.__motor.freq(self.__servo_pwm_freq)

class LED:
    def __init__(self, PinID):
        self.ledPin = Pin(PinID, Pin.OUT)
        self.value = 0 # off
    
    def write(self, value):
        if value == 0:
            self.ledPin.off()
        if value == 1:
            self.ledPin.on()

    def on(self):
        self.ledPin.on()
    
    def off(self):
        self.ledPin.off()

class Receiver:
    def __init__(self, UUID):
        self.UUID = bluetooth.UUID(UUID)
        self.char = None
    
    async def find_char_and_subscribe(self, service):
        char = await service.characteristic(self.UUID)
        await char.subscribe(notify = True)
        self.char = char

    async def listen_and_relay_servo(self, servo):
        while True:
            message = await self.char.notified()
            message = message.decode()
            parsed_message = message.split(",")
            x = int(parsed_message[0])
            x -= 32767 # center at zero
            delta_theta = 35 * x/32767
            angle = 90 + delta_theta
            servo.move(angle)
                
    
    async def listen_and_relay_motors(self, motor_1, motor_2):
        while True:
            message = await self.char.notified()
            message = message.decode()
            parsed_message = message.split(",")
            x = int(parsed_message[0])
            y = int(parsed_message[1])
            motor_1.write((x,y))
            motor_2.write((x,y))
    
    async def listen_and_relay_led(self, led):
        while True:
            message = await self.char.notified()
            message = message.decode()
            if message == "1":
                led.on()
            else:
                led.off()
    
    async def listen_and_relay_blank(self):
        while True:
            message = await self.char.notified()

