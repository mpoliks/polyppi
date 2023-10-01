import colorsys
import math
import time
import blinkt
import random
import numpy as np
from threading import Thread

class LED(object):
    
    def __init__(self):
        self.nexttime = time.time()
        self.spacing = 360.0 / 6.0
        self.hue = 0
        self.flag = False
        self.clear()
        self.persist = True
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
        
        if state == "playing":
            blinkt.set_all(128, 0, 0)
            blinkt.show()
            return
            
        time.sleep(0.06)
        self.persist = True
        t = Thread(target = self.run, args = (state,))

        t.start()
        
    def run(self, state):
        
        while self.persist == True:

            if state == "listening":
                self.hue = int(time.time() * 100) % 360
                for x in range (8):
                    offset = x * self.spacing
                    h = ((self.hue + offset) % 360) / 360.0
                    r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, 1.0, 1.0)]
                    blinkt.set_pixel(x, 0, g, 0)
                blinkt.show()

            if state == "recording":
                if time.time() > self.nexttime:
                    if self.flag == True:
                        for i in range(8):
                            blinkt.set_pixel(i, 0, 0, random.randint(0, 255))
                    if self.flag == False:
                        blinkt.set_all(0, 0,0)
                    self.flag = not self.flag                      
                    blinkt.show()
                    self.nexttime = time.time() + random.uniform(0.001, 0.05)
                        
            if state == "triggered":
                if time.time() > self.nexttime:
                    blinkt.set_all(random.randint(0, 255), 0, random.randint(0, 255))                     
                    blinkt.show()
                    self.nexttime = time.time() + random.uniform(0.001, 0.05)            


            if state == "low_batt":
                if time.time() > self.nexttime:
                    blinkt.set_all(128, 0, 128)
                    blinkt.show()
                    self.nexttime = time.time() + 5000

            if state == "connecting":
                blinkt.set_all(0, random.randint(0, 128), 0)
                blinkt.show()
