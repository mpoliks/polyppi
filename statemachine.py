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
    gDrive = None
    
    boot_manager = BootManager()
    led = LED()
    logging.info("Initializing LEDs")
    led.update("connecting")
    logging.info("Initializing Battery")
    battery = Battery(bus, address)

    if not test_mode:
        try:    
            logging.info("Setting Up GDrive")
            gDrive = GDriveSetup()    
            drive = gDrive.drive
            
        except:
            logging.error("No Internet Connection")
            test_mode = True
            led.update("err")
    
    boot_manager.populate(gDrive, led)

    listener = RMSListener(drive, upload_folder, test_mode)
    player = FilePlayback()

    if not test_mode:
        schedule.every().hour.at(":20").do(boot_manager.reset)
        schedule.every().hour.at(":21").do(boot_manager.pull_vitals, listener, player, battery)
        schedule.every().hour.at(":22").do(boot_manager.reset)
        schedule.every().hour.at(":23").do(boot_manager.upload_logs, gDrive)
        schedule.every().hour.at(":24").do(boot_manager.reset)
        schedule.every().day.at("00:25").do(boot_manager.stall, listener, player)
        schedule.every().day.at("00:26").do(boot_manager.reset)
        schedule.every().day.at("00:27").do(boot_manager.populate, gDrive, led)
        schedule.every().day.at("00:28").do(boot_manager.reset)

    time.sleep(1)
    return(listener, player, led, battery, boot_manager)



def loop(listener, player, led, battery, boot_manager, previous_status = None):
    
    global status
    time_threshold = 0
    batt_level = 100
    
    while(1):
        
        #schedule.run_pending()
        
        if boot_manager.status == "holding": 
            status = "holding"
        if boot_manager.status != "holding":
            if ((time.time() - time_threshold >= 1.0)):  
                schedule.run_pending() 
                #print(status)
                time_threshold = time.time()
                try:
                    status = battery.charge_status()
                except:
                    logging.error("Battery Charge Detection Read Failed")
                    led.update("err")
                if status != previous_status:
                    logging.info("Charge Change Detected, Status = " + str(status))
                    battery.vitals["transition_events"] += 1
                    transition_flag = True
                try:
                    batt_level = battery.charge_level()
                except:
                    logging.error("Battery Charge Read Failed")

        match status:

            case "holding": 
                transition_flag = True
                
                continue

            case "listening":
                if transition_flag:
                    if previous_status == "listening": 
                        while player.fadeOut() == False: pass
                    logging.info("Transitioning into Listening Mode")
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
                    logging.info("Transition into Playing Mode")
                    player.play()
                    transition_flag = False
                if player.is_streaming() == False:
                    logging.info("Looping Audio")
                    player.vitals["files_played"] + 1
                    player.killStream()
                    player.play()
                if batt_level >= 30: led.update("playing")
                if batt_level < 30: led.update ("low_batt")


if __name__ == "__main__":

    print("*--HALTING TO ALLOW FOR CONNECTION TO COMPLETE--*")
    listener, player, led, battery, boot_manager  = setup()

    print("*--INITIALIZED AND RUNNING--*")
    logging.info("Successfully Started Running")
    loop(listener, player, led, battery, boot_manager)
    
    
        
