import colorsys
import math
import time
import blinkt
import random
import numpy as np
from threading import Thread

class LEDController(object):
    
    def __init__(self):
        self.nexttime = time.time()
        self.spacing = 360.0 / 6.0
        self.hue = 0
        self.flag = False
        self.clear()
        self.persist = False
        self.previous_state = None
        t = Thread(target=self.update)
        t.start()
    
    def clear (self):
        blinkt.clear()
        blinkt.show()
        
    def update(self, state):
        if self.previous_state == state: return
        
        self.previous_state = state
        self.persist = False
            
        time.sleep(0.06)
        self.persist = True
        
        t = Thread(target = self.run, args = (state,))

        t.start()
        
    def run(self, state):
        
        while self.persist == True:
        
                if state == "inert":
                    self.hue = int(time.time() * 100) % 360
                    for x in range (8):
                        offset = x * self.spacing
                        h = ((self.hue + offset) % 360) / 360.0
                        r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, 1.0, 1.0)]
                        blinkt.set_pixel(x, g, g, g)
                    blinkt.show()
                        
                if state == "triggered":
                    if time.time() > self.nexttime:
                        temp = random.randint(0, 255)
                        blinkt.set_all(temp, temp, temp)                     
                        blinkt.show()
                        self.nexttime = time.time() + random.uniform(0.001, 0.05)            


