#!/usr/bin/python

import os, shutil, sys
import logging, schedule, time, datetime
from multiprocessing import Process
from lib.audio_fw import *
from lib.led_fw import * 
from lib.pump_fw import *
creature = "POLYP"

test_mode = False ## Test Mode disables connectivity.
status = None 

logs_dir = dir_path + "/logs/"
log_file = logs_dir + "log.log"

def main():
    
    with open(log_file, "w"): pass
    
    #logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    logging.basicConfig(filename=log_file, format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)
    logging.info("PID = " + str(os.getpid()))
    
    logging.info(creature)
    pumpController = None
    ledController = None
    
    if creature == "HYDRA": 
        logging.info("Initializing Pumps")
        pumpController = PumpBehavior()
        time.sleep(20)
    if creature == "POLYP":
        logging.info("Initializing LEDs")
        ledController = LEDController()

    player = FilePlayback()
    listener = RMSListener()
    time.sleep(2)
    
    while (1):
        activity = listener.listen()
        player.loop()
        time.sleep(0.1)
        if creature == "HYDRA":
            pumpController.update(activity)
        if creature == "POLYP":
            ledController.update(activity)

if __name__ == "__main__": main()
    
    
    
        
