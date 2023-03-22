import os, smbus, logging, schedule, time
from datetime import datetime
from filemgmt_fw import *
from audio_fw import *

## Battery Management:
bus=smbus.SMBus(1)
address = 0x57

## File Management:
pi_id = "R3vE20"
test_mode = False
download_folder = '101FNH6ERnutThe6ztVLF8U11UnT5fybD'
upload_folder = '1R8iCvcadFcgn3KGWdO_O4vAN-qa_YGig'
log_folder = '1_RQT4sVP3-KD6JX-G5wiDPwxYsPQ8y5O'
dir_path = os.path.dirname(os.path.realpath(__file__))
playback_dir = dir_path + "/playback/"
recordings_dir = dir_path + "/recordings/"
logs_dir = dir_path + "/logs/"
logging.basicConfig(filename='logs/log.log', format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)

## Audio Settings
channels = 1
sample_rate = 48000
block_freq = 0.5 #frequency of input monitor
frames_per_block = int(sample_rate*block_freq)
rms_thresh = 0.25 #amp threshold over which presence is determined
rec_block_count = 2 #recording starts
write_block_count = 10 #recording ends
volume = 90 #volume in % of playback
write_base = "rec_" #filename base for recordings

def charge_status():
    if (bus.read_byte_data(address, 0x02) & (1<<7)):
        return True
    return False

def calibrate_battery():
    bus.write_byte_data(address, 0x0b, 0x29) #turn off write protection
    time.sleep (0.01)
    bus.write_byte_data(address, 0x20, 0x48) #turn on SCL wake, charge protection
    time.sleep (0.01)
    if bus.read_byte_data(address, 0x20) == 0x48:
        logging.info("OK: Battery Initialized Correctly")
    else:
        logging.error("ERR: Battery Not Set Correctly!")
        logging.error(bus.read_byte_data(address, 0x20))

def upload_logs(drive):
    fileindex = log_path + "/" + pi_id + str(datetime.now()) + ".log"
    os.rename (log_path + "/log.log", fileindex)
    print(fileindex)
    file1 = drive.CreateFile({'parents': [{'id': log_folder}]})
    file1.SetContentFile(fileindex)
    file1.Upload()
    logging.info("LogFile Upload Complete")
    os.remove(fileindex)

def setup():
    calibrate_battery()
    drive = None    
    if not test_mode:
        logging.info("Initializing!")        
        gDrive = GDriveSetup()
        if(len(os.listdir(playback_dir)) == 0):
            gDrive.file_download(download_folder, playback_dir)            
        drive = gDrive.drive
        schedule.every().hour.do(upload_logs, drive)
    listener = RMSListener(channels, sample_rate, frames_per_block, write_base, drive, upload_folder, test_mode)
    player = FilePlayback()
    time.sleep(1)
    return(listener, player)
   
def loop(listener, player, previous_status):
    while(1):
        time.sleep(0.2)
        status = charge_status()
        if status != previous_status:
            logging.info("Charge Change Detected, Status = " + str(status))
        if status:
            if status != previous_status:
                while player.fadeOut() == False:
                    time.sleep(0.01)
                previous_status = status
                listener.start()
            listener.listen(rms_thresh, rec_block_count, write_block_count)
        if status == False:
            if status != previous_status: 
                if listener.is_streaming(): listener.stop()
                previous_status = status
                player.play(playback_dir, volume)
            if player.is_streaming() == False:
                logging.info("Looping Audio")
                player.killStream()
                player.play(playback_dir, volume)

if __name__ == "__main__":
    logging.info("PID = " + str(os.getpid()))
    print("*--HALTING TO ALLOW FOR CONNECTION TO COMPLETE--*")
    previous_status = None
    listener, player = setup()
    print("*--INITIALIZED AND RUNNING--*")
    logging.info("Successfully Started Running")
    loop(listener, player, previous_status)
    
    
        
