# main.py -- put your code here!

import machine
import time

led = machine.Pin(25, machine.Pin.OUT)

while True:
    led.toggle()
    time.sleep(0.5)
