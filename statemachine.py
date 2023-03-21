from filemgmt_fw import *
from audio_fw import *
import smbus

## Battery Management:
bus=smbus.SMBus(1)
address = 0x57

## File Management:
test_mode = False
download_folder = '101FNH6ERnutThe6ztVLF8U11UnT5fybD'
upload_folder = '1R8iCvcadFcgn3KGWdO_O4vAN-qa_YGig'
playback_dir = "/home/marek/Desktop/polyppi/playback/"
recordings_dir = "/home/marek/Desktop/polyppi/recordings/"

## Audio Settings
channels = 1
sample_rate = 48000
block_freq = 0.5 #frequency of input monitor
frames_per_block = int(sample_rate*block_freq)
rms_thresh = 0.25 #amp threshold over which presence is determined
rec_block_count = 2 #recording starts
write_block_count = 10 #recording ends
volume = 70 #volume in % of playback
write_base = "rec_" #filename base for recordings

def charge_status():
    if bus.read_byte_data(address, 0x02) == 236:
        return True
    return False

def setup():
    bus.write_byte_data(address, 0x0b, 0x29) #turn off write protection
    time.sleep (0.01)
    print(bus.read_byte_data(address, 0x0b))
    bus.write_byte_data(address, 0x20, 0x48) #turn on SCL wake, charge protection
    time.sleep (0.01)
    if bus.read_byte_data(address, 0x20) == 0x48:
        print("OK: Battery Initialized Correctly")
    else:
        print ("ERR: Battery Not Set Correctly!")
        print (bus.read_byte_data(address, 0x20))
    drive = None
    if not test_mode:
        print("Initializing!")        
        gDrive = GDriveSetup()
        if(len(os.listdir(playback_dir)) == 0):
            gDrive.file_download(download_folder, playback_dir)            
        drive = gDrive.drive  
    listener = RMSListener(channels, sample_rate, frames_per_block, write_base, drive, upload_folder, test_mode)
    player = FilePlayback()
    time.sleep(1)
    return(listener, player)
   
def loop(listener, player, previous_status):
    while(1):
        time.sleep(0.2)
        status = charge_status()
        if status != previous_status: print("OK: Transitioning!")
        if status:
            if status != previous_status:
                if not player.is_streaming(): previous_status = status
                if player.is_streaming(): player.fadeOut()
                ## find another way to call this in a loop!
                listener.start() 
            listener.listen(rms_thresh, rec_block_count, write_block_count)
        if status == False:
            if status != previous_status: 
                if listener.is_streaming(): listener.stop()
                previous_status = status
                player.play(playback_dir, volume)
            if player.is_streaming() == False:
                print("OK: Looping")
                player.killStream()
                player.play(playback_dir, volume)

if __name__ == "__main__":
    previous_status = None
    listener, player = setup()
    loop(listener, player, previous_status)
    
    
        
