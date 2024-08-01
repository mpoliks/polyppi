#!/usr/bin/env python3

import os
import random
import time
from pydub import AudioSegment
from pydub.playback import play
import logging

# Configure logging
logging.basicConfig(filename='/var/log/loop_audio.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

# Set the directory to search within the subdirectory 'epflsync'
AUDIO_DIR = '/home/polyppi/raspberrypi-firmware/synced_files/epflsync'

def get_random_audio_file(directory):
    audio_files = []
    for root, dirs, files in os.walk(directory):
        audio_files.extend([os.path.join(root, f) for f in files if f.endswith(('.mp3', '.wav', '.ogg', '.flac', '.aiff'))])
    
    if not audio_files:
        return None
    return random.choice(audio_files)

def main():
    logging.info('Script started')
    while True:
        try:
            audio_file = get_random_audio_file(AUDIO_DIR)
            if audio_file:
                logging.info(f'Playing {audio_file}')
                audio = AudioSegment.from_file(audio_file)
                play(audio)
            else:
                logging.warning('No audio files found in the directory. Retrying in 10 seconds.')
        except Exception as e:
            logging.error('Error playing audio: %s', str(e))
        time.sleep(10)

if __name__ == '__main__':
    main()
