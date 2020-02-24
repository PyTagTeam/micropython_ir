# ir_tx_test.py Test for nonblocking NEC/RC-5/RC-6 mode 0 IR blaster.

# Released under the MIT License (MIT). See LICENSE.

# Copyright (c) 2020 Peter Hinch

# Implements a 2-button remote control on a Pyboard

from pyb import Pin, LED
import uasyncio as asyncio
from aswitch import Switch, Delay_ms
from ir_tx import NEC, RC5, RC6_M0

loop = asyncio.get_event_loop()

class Rbutton:
    toggle = 1  # toggle is ignored in NEC mode
    def __init__(self, irb, pin, addr, data, rep_code=False):
        self.irb = irb
        self.sw = Switch(pin)
        self.addr = addr
        self.data = data
        self.rep_code = rep_code
        self.sw.close_func(self.cfunc)
        self.sw.open_func(self.ofunc)
        self.tim = Delay_ms(self.repeat)

    def cfunc(self):  # Button push: send data
        self.irb.transmit(self.addr, self.data, Rbutton.toggle)
        # Auto repeat
        self.tim.trigger(108)

    def ofunc(self):  # Button release: cancel repeat timer
        self.tim.stop()
        Rbutton.toggle ^= 1  # Toggle control

    async def repeat(self):
        await asyncio.sleep(0)  # Let timer stop before retriggering
        if not self.sw():  # Button is still pressed: retrigger
            self.tim.trigger(108)
            if self.rep_code:
                self.irb.repeat()  # NEC special case: send REPEAT code
            else:
                self.irb.transmit(self.addr, self.data, Rbutton.toggle)

async def main(proto):
    # Test uses a 38KHz carrier. Some Philips systems use 36KHz.
    # If button is held down normal behaviour is to retransmit
    # but most NEC models send a RPEAT code
    rep_code = False  # Don't care for RC-X. NEC protocol only.
    pin = Pin('X1')
    if not proto:
        irb = NEC(pin)  # Default NEC freq == 38KHz
        # Option to send REPEAT code. Most remotes do this.
        rep_code = True
    elif proto == 5:
        irb = RC5(pin, 38000)
    elif proto == 6:
        irb = RC6_M0(pin, 38000)

    b = []  # Rbutton instances
    b.append(Rbutton(irb, Pin('X3', Pin.IN, Pin.PULL_UP), 0x1, 0x7, rep_code))
    b.append(Rbutton(irb, Pin('X4', Pin.IN, Pin.PULL_UP), 0x10, 0xb, rep_code))
    led = LED(1)
    while True:
        await asyncio.sleep_ms(500)  # Obligatory flashing LED.
        led.toggle()

s = '''Test for IR transmitter. Run:
ir_tx_test.test() for NEC protocol
ir_tx_test.test(5) for RC-5 protocol
ir_tx_test.test(6) for RC-6 mode 0.

Ground X3 to send addr 1 data 7
Ground X4 to send addr 0x10 data 0x0b.'''
print(s)

def test(proto=0):
    loop.run_until_complete(main(proto))