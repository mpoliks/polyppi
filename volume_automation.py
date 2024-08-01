#!/usr/bin/env python3

import numpy as np
import time
import logging
import os
import random
import alsaaudio

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Log to file
file_handler = logging.FileHandler('/var/log/volume_automation.log')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(file_formatter)

# Log to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
console_handler.setFormatter(console_formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Max volume level (percentage)
MAX_LEVEL = 100

class FilePlayback:
    def __init__(self):
        logger.info("Initializing Mixer")
        logger.info(alsaaudio.mixers())
        logger.info(alsaaudio.cards())
        logger.info(alsaaudio.pcms())
        self.m = None
        for mixername in alsaaudio.mixers():
            logger.info("Trying " + str(mixername))
            if str(mixername) in ["Digital", "Analogue", "PCM"]:
                logger.info("Mixername " + str(mixername) + " selected")
                self.m = alsaaudio.Mixer(mixername)
                break
        if not self.m:
            logger.error("Failed to initialize any suitable mixer")
        logger.info("Initialized File Player")

    def set_volume(self, level):
        if self.m:
            self.m.setvolume(level)
        else:
            logger.error("No mixer available to set volume")

def adjust_volume(level):
    volume_percentage = int(level * MAX_LEVEL)
    player.set_volume(volume_percentage)

def event_a():
    logger.info("Starting event A: series of sweeps")
    num_sweeps = random.randint(1, 5)
    for _ in range(num_sweeps):
        duration = random.uniform(1, 4)
        for t in np.linspace(0, 1, int(duration * 50)):  # 50 updates per second
            adjust_volume(t)
            time.sleep(0.02)  # 20 ms
        for t in np.linspace(1, 0, int(duration * 50)):
            adjust_volume(t)
            time.sleep(0.02)
    logger.info("Ending event A")

def event_b():
    logger.info("Starting event B: plateau")
    duration = random.uniform(10, 100)
    adjust_volume(1)
    time.sleep(duration)
    adjust_volume(0)
    logger.info("Ending event B")

def event_c():
    logger.info("Starting event C: assemblage of sweeps")
    total_duration = random.uniform(30, 200)
    end_time = time.time() + total_duration
    while time.time() < end_time:
        duration = random.uniform(1, 10)
        max_level = random.uniform(0.5, 1.0)
        for t in np.linspace(0, max_level, int(duration * 50)):
            adjust_volume(t)
            time.sleep(0.02)
        for t in np.linspace(max_level, 0, int(duration * 50)):
            adjust_volume(t)
            time.sleep(0.02)
    logger.info("Ending event C")

def main():
    global player
    player = FilePlayback()
    logger.info('Volume automation script started')
    while True:
        try:
            event_type = random.choices(['a', 'b', 'c'], weights=[0.1, 0.6, 0.3])[0]
            if event_type == 'a':
                event_a()
            elif event_type == 'b':
                event_b()
            else:
                event_c()

            # Sleep for a random duration between 20 and 240 seconds
            sleep_duration = random.uniform(20, 240)
            logger.info(f'Sleeping for {sleep_duration} seconds')
            time.sleep(sleep_duration)
        except Exception as e:
            logger.error(f'Error in volume automation: {str(e)}')

if __name__ == '__main__':
    main()
