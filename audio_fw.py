#!/usr/bin/env python3

import os
import random
import time
import logging
import numpy as np
import alsaaudio
import wave
import pyaudio

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Log to file
file_handler = logging.FileHandler('/var/log/audio_fw.log')
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

# Set the directory to search within the subdirectory 'epflsync'
AUDIO_DIR = '/home/polyppi/raspberrypi-firmware/synced_files/epflsync'

# Max volume level (percentage)
MAX_LEVEL = 100

class FilePlayback(object):
    def __init__(self):
        logging.info("Initializing Mixer")
        logging.info(alsaaudio.mixers())
        logging.info(alsaaudio.cards())
        logging.info(alsaaudio.pcms())
        self.m = None
        for mixername in alsaaudio.mixers():
            logging.info("Trying " + str(mixername))
            if str(mixername) in ["Digital"]:
                logging.info("Mixername " + str(mixername) + " selected")
                self.m = alsaaudio.Mixer(mixername)
                break
        if not self.m:
            logging.error("Failed to initialize any suitable mixer")
        self.stream = None
        self.volume = None
        logging.info("Initialized File Player")

    def set_volume(self, level):
        if self.m:
            self.m.setvolume(level)
        else:
            logging.error("No mixer available to set volume")

    def play(self):
        logging.info("Starting Playback")
        self.volume = 100  # Assuming a constant playback volume for simplicity
        logging.info(self.volume)
        logging.info(self.m)
        self.m.setvolume(self.volume)
        logging.info("Selecting from " + str(AUDIO_DIR))
        playfile = AUDIO_DIR + "/" + random.choice(os.listdir(AUDIO_DIR))
        logging.info("Selected: " + str(playfile))
        self.wf = wave.open(playfile, 'rb')
        logging.info("Opened Playfile")
        self.pa = pyaudio.PyAudio()
        logging.info("Playing back " + playfile)
        self.stream = self.pa.open(format=self.pa.get_format_from_width(self.wf.getsampwidth()),
                                   channels=self.wf.getnchannels(),
                                   rate=self.wf.getframerate(),
                                   output=True,
                                   stream_callback=self.callback)

    def callback(self, in_data, frame_count, time_info, status):
        data = self.wf.readframes(frame_count)
        return (data, pyaudio.paContinue)

    def is_streaming(self):
        try:
            if self.stream is None: return False
            if self.stream.is_active(): return True
        except OSError as e:
            return False
        return False

    def kill_stream(self):
        logging.info("Killing Playback Stream")
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()

def adjust_volume(level):
    volume_percentage = int(level * MAX_LEVEL)
    logger.debug(f"Setting volume to {volume_percentage}%")
    player.set_volume(volume_percentage)

def event_a():
    logger.info("Starting event A: series of sweeps")
    num_sweeps = random.randint(1, 5)
    for _ in range(num_sweeps):
        duration = random.uniform(1, 4)
        steps = int(duration * 50)  # 50 updates per second
        
        # Parabolic sweep up
        for i in range(steps):
            t = i / steps
            volume_level = (4 * t * (1 - t))  # Quadratic function normalized to peak at 1
            adjust_volume(volume_level)
            time.sleep(0.02)  # 20 ms
        
        # Parabolic sweep down
        for i in range(steps):
            t = i / steps
            volume_level = (4 * t * (1 - t))  # Quadratic function normalized to peak at 1
            adjust_volume(volume_level)
            time.sleep(0.02)
    
    logger.info("Ending event A")


def event_b():
    logger.info("Starting event B: plateau")
    
    fade_in_duration = random.uniform(2, 20)
    plateau_duration = random.uniform(10, 100)
    fade_out_duration = random.uniform(2, 20)
    
    logger.info(f"Fade-in duration: {fade_in_duration} seconds")
    logger.info(f"Plateau duration: {plateau_duration} seconds")
    logger.info(f"Fade-out duration: {fade_out_duration} seconds")
    
    # Fade-in
    for t in np.linspace(0, 1, int(fade_in_duration * 50)):  # 50 updates per second
        adjust_volume(t)
        time.sleep(0.02)  # 20 ms
    
    # Plateau
    adjust_volume(1)
    time.sleep(plateau_duration)
    
    # Fade-out
    for t in np.linspace(1, 0, int(fade_out_duration * 50)):
        adjust_volume(t)
        time.sleep(0.02)
    
    adjust_volume(0)
    logger.info("Ending event B")

def event_c():
    logger.info("Starting event C: assemblage of sweeps")
    total_duration = random.uniform(30, 200)
    end_time = time.time() + total_duration
    while time.time() < end_time:
        duration = random.uniform(1, 10)
        max_level = random.uniform(0.5, 1.0)
        steps = int(duration * 50)
        
        # Upward sweep
        up_sweep = quadratic_adjustment(0, max_level, duration, steps)
        for t in up_sweep:
            adjust_volume(t)
            time.sleep(0.02)
        
        # Downward sweep
        down_sweep = quadratic_adjustment(max_level, 0, duration, steps)
        for t in down_sweep:
            adjust_volume(t)
            time.sleep(0.02)

        # Optional: Add a brief pause between sweeps
        if random.choice([True, False]):
            pause_duration = random.uniform(0.1, 1.0)
            logger.debug(f"Pausing for {pause_duration} seconds")
            time.sleep(pause_duration)

    logger.info("Ending event C")

def main():
    global player
    player = FilePlayback()
    logger.info('Audio firmware script started')

    while True:
        
        if not player.is_streaming(): player.play()

        try:
            # Select and execute a volume automation event
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
            logger.error(f'Error in audio firmware script: {str(e)}')

if __name__ == '__main__':
    main()
