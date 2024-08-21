#!/usr/bin/env python3

import os
import random
import time
import logging
import json
import alsaaudio
import wave
import pyaudio
import requests
import schedule
import pwd
import numpy as np
import uuid
import subprocess
from datetime import datetime, timedelta

# Unique identifier for each run
RUN_ID = str(uuid.uuid4())

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Log to file
file_handler = logging.FileHandler('/var/log/audio_fw.log')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s [RUN_ID: ' + RUN_ID + ']')
file_handler.setFormatter(file_formatter)

# Log to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s [RUN_ID: ' + RUN_ID + ']')
console_handler.setFormatter(console_formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

# Set the directory to search within the subdirectory 'epflsync'
AUDIO_DIR = os.path.expanduser('~/raspberrypi-firmware/synced_files/epflsync')

# Configuration file path
CONFIG_FILE = os.path.expanduser('~/raspberrypi-firmware/config.json')
INIT_FLAG_FILE = '/var/log/audio_fw_initialized.flag'
LAST_SYNC_FILE = '/var/log/last_sync_time.flag'

MAX_LEVEL = 100  # Initialize MAX_LEVEL with a default value
DENSITY = "medium"  # Initialize DENSITY with a default value

def load_config():
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f'Configuration file not found: {CONFIG_FILE}')
        return {"MAX_VOLUME": 100, "DENSITY": "medium"}

def reload_config():
    global MAX_LEVEL, DENSITY
    logger.debug("Running reload_config")
    config = load_config()
    new_max_level = config.get('MAX_VOLUME', 100)
    new_density = config.get('DENSITY', "medium")

    if new_max_level != MAX_LEVEL:
        logger.info(f'MAX_VOLUME changed from {MAX_LEVEL} to {new_max_level}')
        message = f'MAX_VOLUME changed from {MAX_LEVEL} to {new_max_level} on {os.uname()[1]} by {pwd.getpwuid(os.getuid()).pw_name}.'
        send_discord_message(DISCORD_HEARTBEAT_WEBHOOK, message)
        MAX_LEVEL = new_max_level
    else:
        logger.info(f'MAX_VOLUME remains at {MAX_LEVEL}')

    if new_density != DENSITY:
        logger.info(f'DENSITY changed from {DENSITY} to {new_density}')
        message = f'DENSITY changed from {DENSITY} to {new_density} on {os.uname()[1]} by {pwd.getpwuid(os.getuid()).pw_name}.'
        send_discord_message(DISCORD_HEARTBEAT_WEBHOOK, message)
        DENSITY = new_density
    else:
        logger.info(f'DENSITY remains at {DENSITY}')

    logger.debug("Completed reload_config")

def sync_to_gcp():
    logger.info("Starting sync to GCP...")
    
    GCP_USER = "mpoliks"
    GCP_HOST = "34.66.128.13"
    GCP_PATH = "/home/mpoliks/synced_files/"
    LOCAL_PATH = os.path.expanduser('~/raspberrypi-firmware/synced_files/')
    
    try:
        rsync_command = [
            "rsync", "-avz", "--progress", "--delete", "-e", "ssh -i ~/.ssh/id_rsa",
            f"{GCP_USER}@{GCP_HOST}:{GCP_PATH}", LOCAL_PATH
        ]
        result = subprocess.run(rsync_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("GCP sync completed successfully.")
            send_discord_message(DISCORD_HEARTBEAT_WEBHOOK, f"GCP sync completed successfully on {pwd.getpwuid(os.getuid()).pw_name}.")
            with open(LAST_SYNC_FILE, 'w') as f:
                f.write(datetime.now().isoformat())
        else:
            logger.error(f"GCP sync failed: {result.stderr}")
            send_discord_message(DISCORD_CRASH_WEBHOOK, f"GCP sync failed: {result.stderr}")
    except Exception as e:
        logger.error(f"Error during GCP sync: {str(e)}")
        send_discord_message(DISCORD_CRASH_WEBHOOK, f"Error during GCP sync: {str(e)}")

def should_sync():
    try:
        if os.path.exists(LAST_SYNC_FILE):
            with open(LAST_SYNC_FILE, 'r') as f:
                last_sync_time = datetime.fromisoformat(f.read().strip())
            if datetime.now() - last_sync_time >= timedelta(hours=1):
                return True
        else:
            return True  # If the file doesn't exist, perform the sync
    except Exception as e:
        logger.error(f"Error checking last sync time: {str(e)}")
        return True  # In case of error, attempt to sync

    return False

DISCORD_INIT_WEBHOOK = os.getenv('DISCORD_INIT_WEBHOOK')
DISCORD_CRASH_WEBHOOK = os.getenv('DISCORD_CRASH_WEBHOOK')
DISCORD_HEARTBEAT_WEBHOOK = os.getenv('DISCORD_HEARTBEAT_WEBHOOK')

def get_cpu_temperature():
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp = int(f.read()) / 1000.0  # Convert from millidegrees to degrees
            return temp
    except FileNotFoundError:
        logger.error("Could not read CPU temperature: File not found")
        return None

def send_discord_message(webhook_url, message):
    data = {"content": message}
    response = requests.post(webhook_url, json=data)
    if response.status_code != 204:
        logger.error(f"Failed to send message to Discord: {response.status_code}, {response.text}")
    else:
        logger.info(f"Successfully sent message to Discord: {message}")

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

    def play(self, retries=5, backoff_factor=1):
        attempt = 0
        logging.debug("Entered Playback Function")
        while attempt < retries:
            logging.info(f"Starting Playback, attempt {attempt + 1}")
            self.volume = 100  # Assuming a constant playback volume for simplicity
            logging.info(self.volume)
            logging.info(self.m)
            try:
                self.m.setvolume(self.volume)
                logging.info(f"Selecting from {AUDIO_DIR} with density {DENSITY}")
                playfile = AUDIO_DIR + "/" + random.choice(os.listdir(AUDIO_DIR))
                logging.info(f"Selected: {playfile}")
                # Check if the file is a valid WAV file
                with open(playfile, 'rb') as f:
                    if f.read(4) != b'RIFF':
                        logging.error(f"File does not start with RIFF id: {playfile}")
                        send_discord_message(DISCORD_CRASH_WEBHOOK, f"File does not start with RIFF id: {playfile}")
                        raise ValueError("Invalid WAV file format")
                self.wf = wave.open(playfile, 'rb')
                logging.info("Opened Playfile")
                self.pa = pyaudio.PyAudio()
                logging.info(f"Playing back {playfile} with density {DENSITY}")
                self.stream = self.pa.open(format=self.pa.get_format_from_width(self.wf.getsampwidth()),
                                           channels=self.wf.getnchannels(),
                                           rate=self.wf.getframerate(),
                                           output=True,
                                           stream_callback=self.callback)
                return  # Exit the function if playback starts successfully
            except Exception as e:
                logging.error(f"Error during playback initialization: {str(e)}")
                send_discord_message(DISCORD_CRASH_WEBHOOK, f"Error during playback initialization: {str(e)}")
                attempt += 1
                if attempt < retries:
                    sleep_time = backoff_factor * (2 ** attempt)
                    logging.info(f"Retrying playback initialization in {sleep_time} seconds")
                    time.sleep(sleep_time)
                else:
                    logging.error("Maximum retries reached, giving up on playback initialization")

    def callback(self, in_data, frame_count, time_info, status):
        try:
            data = self.wf.readframes(frame_count)
            return (data, pyaudio.paContinue)
        except Exception as e:
            logging.error(f"Error in playback callback: {str(e)}")
            send_discord_message(DISCORD_CRASH_WEBHOOK, f"Error in playback callback: {str(e)}")
            return (None, pyaudio.paAbort)

    def is_streaming(self):
        try:
            if self.stream is None: return False
            if self.stream.is_active(): return True
        except OSError as e:
            logging.error(f"OSError in is_streaming: {str(e)}")
            return False
        return False

    def kill_stream(self):
        logging.info("Killing Playback Stream")
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.pa.terminate()

def adjust_volume(level):
    volume_percentage = int(level * MAX_LEVEL)
    player.set_volume(volume_percentage)

def event_a():
    logger.info("Starting event A: series of sweeps")
    
    if DENSITY == "high":
        num_sweeps = random.randint(3, 9)
    elif DENSITY == "medium":
        num_sweeps = random.randint(1, 6)
    elif DENSITY == "low":
        num_sweeps = random.randint(1, 3)
    else:
        num_sweeps = random.randint(1, 5)  # Default if DENSITY is unexpected

    for _ in range(num_sweeps):
        duration = random.uniform(1, 4)
        steps = int(duration * 50)  # 50 updates per second
        
        # Parabolic sweep up
        for i in range(steps):
            t = i / steps
            volume_level = (4 * t * (1 - t))  # Quadratic function normalized to peak at 1
            adjust_volume(volume_level)
            time.sleep(0.02)  # 20 ms

        # Swell at the top
        swell_duration = random.uniform(0.5, 2.0)  # Swell duration between 0.5 and 2 seconds
        logger.debug(f"Swell duration at top: {swell_duration} seconds")
        time.sleep(swell_duration)
        
        # Parabolic sweep down
        for i in range(steps):
            t = i / steps
            volume_level = (4 * t * (1 - t))  # Quadratic function normalized to peak at 1
            adjust_volume(volume_level)
            time.sleep(0.02)
    
    logger.info("Ending event A")


def event_b():
    logger.info("Starting event B: plateau")
    
    if DENSITY == "high" or DENSITY == "medium": 
        fade_in_duration = random.uniform(2, 20)
        plateau_duration = random.uniform(30, 100)
        fade_out_duration = random.uniform(2, 20)
    elif DENSITY == "low": 
        fade_in_duration = random.uniform(2, 20)
        plateau_duration = random.uniform(10, 30)
        fade_out_duration = random.uniform(2, 20)
    else:
        fade_in_duration = random.uniform(2, 15)  # Default values if DENSITY is unexpected
        plateau_duration = random.uniform(20, 50)
        fade_out_duration = random.uniform(2, 15)

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
        steps = int(duration * 50)  # 50 updates per second

        # Upward sweep
        up_sweep = [(4 * t * (1 - t)) for t in np.linspace(0, max_level, steps)]
        for volume_level in up_sweep:
            adjust_volume(volume_level)
            time.sleep(0.02)  # 20 ms

        # Pause at the top
        if DENSITY == "high":
            swell_duration = random.uniform(3, 15)
        elif DENSITY == "medium":
            swell_duration = random.uniform(3, 10)        
        elif DENSITY == "low":
            swell_duration = random.uniform(1, 5)
        else:
            swell_duration = random.uniform(1, 10)  # Default if DENSITY is unexpected
        
        logger.debug(f"Swell duration at top: {swell_duration} seconds")
        time.sleep(swell_duration)

        # Downward sweep
        down_sweep = [(4 * t * (1 - t)) for t in np.linspace(max_level, 0, steps)]
        for volume_level in down_sweep:
            adjust_volume(volume_level)
            time.sleep(0.02)  # 20 ms

        # Optional: Add a brief pause between sweeps
        if random.choice([True, False]):
            pause_duration = random.uniform(0.1, 1.0)
            logger.debug(f"Pausing for {pause_duration} seconds")
            time.sleep(pause_duration)

    logger.info("Ending event C")

def heartbeat():
    temperature = get_cpu_temperature()
    if temperature is not None:
        logger.info(f"CPU Temperature: {temperature:.2f}\u00B0C")
    else:
        logger.error("Failed to retrieve CPU temperature")
    send_discord_message(DISCORD_HEARTBEAT_WEBHOOK, f"Heartbeat: Audio firmware script is running on {os.uname()[1]} by {pwd.getpwuid(os.getuid()).pw_name}. Operating temp = {temperature}.")

def main():
    global player
    global MAX_LEVEL, DENSITY
    config = load_config()
    MAX_LEVEL = config.get('MAX_VOLUME', 100)
    DENSITY = config.get('DENSITY', "medium")
    logger.debug(f"Init MAX_LEVEL SET {MAX_LEVEL}. Init DENSITY SET {DENSITY}.")
    player = FilePlayback()  # Corrected assignment
    logger.info('Audio firmware script started')

    # Check and remove the init flag file if it exists
    if os.path.exists(INIT_FLAG_FILE):
        os.remove(INIT_FLAG_FILE)
        logger.info(f"Removed init flag file: {INIT_FLAG_FILE}")

    # Send Discord message if not already sent
    if not os.path.exists(INIT_FLAG_FILE):
        temperature = get_cpu_temperature()
        if temperature is not None:
            logger.info(f"CPU Temperature: {temperature:.2f}\u00B0C")
        else:
            logger.error("Failed to retrieve CPU temperature")
        message = f"Audio firmware script initialized successfully on {os.uname()[1]} by {pwd.getpwuid(os.getuid()).pw_name}. Operating temperature = {temperature}. Density level = {DENSITY} and volume = {MAX_LEVEL}."
        send_discord_message(DISCORD_INIT_WEBHOOK, message)
        with open(INIT_FLAG_FILE, 'w') as f:
            f.write('initialized')

    # Schedule the heartbeat function to run every 24 hours
    schedule.every(2).hours.do(heartbeat)
    logger.debug("made it through first scheduler")
    # Schedule the config reload function to run every 60 seconds
    schedule.every(60).seconds.do(reload_config)
    logger.debug("Playing Back First Audio File")
    player.play()

    while True:
        schedule.run_pending()
        if not player.is_streaming():
            # Check if an hour has passed since the last sync and perform sync if needed
            if should_sync():
                sync_to_gcp()

            player.kill_stream()
            player.play()

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
            if DENSITY == "high":
                sleep_duration = random.uniform(3, 40)
            elif DENSITY == "medium":
                sleep_duration = random.uniform(10, 120)                
            elif DENSITY == "low":
                sleep_duration = random.uniform(20, 240)                
            else:
                sleep_duration = random.uniform(10, 120)  # Default if DENSITY is unexpected
            logger.info(f'Sleeping for {sleep_duration} seconds')
            time.sleep(sleep_duration)
        except Exception as e:
            logger.error(f'Error in audio firmware script: {str(e)}')
            send_discord_message(DISCORD_CRASH_WEBHOOK, f"Error in audio firmware script: {str(e)}")

if __name__ == '__main__':
    main()

