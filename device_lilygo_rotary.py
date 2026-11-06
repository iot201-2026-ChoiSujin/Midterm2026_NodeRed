from IO7FuPython import ConfiguredDevice
import json
import time
import uComMgr32
from machine import Pin
import st7789
import tft_config
import vga2_8x16 as font1
import vga1_bold_16x32 as font2

rotaryA = Pin(43, Pin.IN, Pin.PULL_UP)
rotaryB = Pin(44, Pin.IN, Pin.PULL_UP)

old_encode = 0
right = [13, 32, 20, 1]
left = [10, 2, 23, 31]

value = 0
def rotated(p):
    global old_encode, value, lastPub
    new_state = rotaryA.value() << 1 | rotaryB.value()
    if new_state != old_encode:
        new_combined = old_encode * 10 + new_state
        old_encode = new_state
        if new_combined in right:
            value = (value + 1) if value < 255 else 255
        elif new_combined in left:
            value = (value - 1) if value > 0 else 0
        lastPub = time.ticks_ms() - device.meta['pubInterval'] + 50
        display()

tft = tft_config.config(3, buffer_size=64*64*2)

tft.init()
tft.fill(st7789.BLACK)
tft.text(font2, 'Rotary', 110, 5, st7789.WHITE)
tft.text(font1, 'Target      : ', 65, 70, st7789.WHITE)

def r2t(r):
    # 0.1960784 = (60 - 10) / 255 - 0
    return r * 0.1960784 + 10

def t2r(t):
    # 0.1960784 = (60 - 10) / 255 - 0
    return (t - 10) / 0.1960784

def handleCommand(topic, msg):
    global lastPub, value
    jo = json.loads(str(msg,'utf8'))
    if ("target" in jo['d']):
        value = t2r(int(jo['d']['target']))
        lastPub = - device.meta['pubInterval']
        display()

def display():
    tft.text(font1, f'{round(r2t(value),2):6}', 200, 70, st7789.WHITE)

nic = uComMgr32.startWiFi('io7rotary')
device = ConfiguredDevice()
device.setUserCommand(handleCommand)

device.connect()

lastPub = time.ticks_ms() - device.meta['pubInterval']
display()

rotaryA.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=rotated)
rotaryB.irq(trigger=Pin.IRQ_FALLING | Pin.IRQ_RISING, handler=rotated)

while True:
    if not device.loop():
        tft.deinit()
        break
    if (time.ticks_ms() - device.meta['pubInterval']) > lastPub:
        lastPub = time.ticks_ms()
        device.publishEvent('status',
            json.dumps({
                'd' : {
                        'target': round(r2t(value),2)
                      }
                 }
            )
        )