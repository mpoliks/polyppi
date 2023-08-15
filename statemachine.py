import os, shutil, logging, schedule, time
from lib.filemgmt_fw import *
from lib.audio_fw import *
from lib.led_fw import * 
from lib.power_fw import *

test_mode = False ## Test Mode disables connectivity.
status = None

def setup():
    
    global test_mode
    global status
    drive = None
    boot_manager = BootManager()
    led = LED()
    logging.info("Initializing LEDs")
    led.update("connecting")
    logging.info("Initializing Battery")
    battery = Battery(bus, address)
    
    logging.info("Setting Up GDrive")
    gDrive = GDriveSetup()    
    drive = gDrive.drive
    boot_manager.populate(gDrive, led)

    if not test_mode:
        logging.info("Initializing!")        
        try:

            logging.info("Wiping Filesystem and Downloading")
            

        except:
            logging.error("No Internet Connection")
            test_mode = True
            led.update("err")

    listener = RMSListener(drive, upload_folder, test_mode)
    player = FilePlayback()

    if not test_mode: 
        schedule.every().day.at("04:04").do(status = boot_manager.stall(listener, player))
        schedule.every().day.at("04:08").do(status = boot_manager.wipe(drive, led))
        schedule.every().minute.at(":55").do(boot_manager.pull_vitals(listener, player, battery))
        schedule.every().hour.do(gDrive.upload_logs, drive)


    time.sleep(1)
    return(listener, player, led, battery)



def loop(listener, player, led, battery, previous_status = None):
    
    global status
    time_threshold = 0
    
    while(1):
        # make batt read only when status isn't holding

        match status:

            case "holding":
                continue

            case "listening":
                if transition_flag:
                    while player.fadeOut() == False: pass
                    previous_status = status
                    listener.start()
                    transition_flag = False
                listener.listen()
                if listener.rec_flag == True: led.update("recording")
                if listener.rec_flag == False: led.update("listening")
            
            case "playing":
                if transition_flag: 
                    if listener.is_streaming(): listener.stop()
                    previous_status = status
                    player.play()
                    transition_flag = False
                if player.is_streaming() == False:
                    logging.info("Looping Audio")
                    player.vitals["files_played"] + 1
                    player.killStream()
                    player.play()
                if battery.charge_level() >= 30: led.update("playing")
                if battery.charge_level() < 30: led.update ("low_batt")

        if (time.time() - time_threshold >= (0.2 * 1000)):     
            time_threshold = time.time()
            try:
                status = battery.charge_status()
            except:
                logging.error("Battery Charge Read Failed")
                led.update("err")
            if status != previous_status:
                logging.info("Charge Change Detected, Status = " + str(status))
                battery.vitals["transition_events"] += 1
                transition_flag = True


if __name__ == "__main__":

    print("*--HALTING TO ALLOW FOR CONNECTION TO COMPLETE--*")
    listener, player, led, battery  = setup()

    print("*--INITIALIZED AND RUNNING--*")
    logging.info("Successfully Started Running")
    loop(listener, player, led, battery)
    
    
        
