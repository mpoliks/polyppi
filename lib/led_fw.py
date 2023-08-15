import colorsys
import math
import time
import blinkt
import random
import numpy as np

class LED(object):
    
    def __init__(self):
        self.nexttime = time.time()
        self.flag = False
        self.clear()
    
    def clear (self):
        blinkt.clear()
        blinkt.show()

    def make_gaussian(fwhm):
        x = np.arange(0, blinkt.NUM_PIXELS, 1, float)
        y = x[:, np.newaxis]
        x0, y0 = 3.5, 3.5
        fwhm = fwhm
        gauss = np.exp(-4 * np.log(2) * ((x - x0) ** 2 + (y - y0) ** 2) / fwhm ** 2)
        return gauss

    def update(self, state):
        match state:

            case "err":
                blinkt.set_all(128, 128, 0)
                blinkt.show()
                self.nexttime = time.time() + 1000

            case "listening":
                if time.time() > self.nexttime:

                    for z in list(range(1, 10)[::-1]) + list(range(1, 10)):
                        fwhm = 5.0 / z
                        gauss = self.make_gaussian(fwhm)
                        start = time.time()
                        y = 4

                    for x in range(blinkt.NUM_PIXELS):
                        h = 0.5
                        s = 1.0
                        v = gauss[x, y]
                        rgb = colorsys.hsv_to_rgb(h, s, v)
                        r, g, b = [int(255.0 * i) for i in rgb]
                        blinkt.set_pixel(x, r, g, b)

                    blinkt.show()
                    end = time.time()
                    self.nexttime = time.time() + 40

            case "recording":
                if time.time() > self.nexttime:
                    for i in range(blinkt.NUM_PIXELS):
                        blinkt.setpixel(i, 0, 0, random.randint(0, 255))
                    blinkt.show()
                    self.nexttime = time.time() + random.randint(60, 150)

            case "playing":
                if time.time() > self.nexttime:
                    blinkt.set_all(128, 0, 0)
                    blinkt.show()
                    self.nexttime = time.time() + 1000

            case "low_batt":
                if time.time() > self.nexttime:
                    blinkt.set_all(128, 0, 128)
                    blinkt.show()
                    self.nexttime = time.time() + 1000

            case "connecting":
                blinkt.set_all(0, 128, 0)
                blinkt.show()