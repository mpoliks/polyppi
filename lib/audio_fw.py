import pyaudio, wave, alsaaudio
import math, struct, time, random
import os, logging

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

def get_rms(block):
    count = len(block)/2
    format = "%dh"%(count)
    shorts = struct.unpack(format, block )
    sum_squares = 0.0
    for sample in shorts:
        n = sample * (1.0/32768.0)
        sum_squares += n*n
    return math.sqrt(sum_squares / count)

class RMSListener(object):
    def __init__(self, write_base, drive, drive_loc, to_upload):
        logging.info("Listener Initialized")
        self.frames = []
        self.itercount = 0        
        self.recflag = 0
        self.rmscount = 0
        self.errorcount = 0        
        self.audio_format = pyaudio.paInt16
        self.channels = channels
        self.rate = sample_rate
        self.fpb = frames_per_block
        self.write_base = write_base
        self.write_time = 0
        self.drive = drive
        self.upload_folder_id = drive_loc
        self.to_upload = not to_upload        
        self.pa = pyaudio.PyAudio()
        self.device_index = self.find_input_device()
        self.stream = None

    def stop(self):
        try:
            self.stream.close()
        except IOError as e:
            self.errorcount += 1
            logging.error( "(%d) Error pausing stream: %s"%(self.errorcount,e) )
        
    def start(self):
        self.stream = self.open_mic_stream()

    def find_input_device(self):
        device_index = None            
        for i in range( self.pa.get_device_count() ):     
            devinfo = self.pa.get_device_info_by_index(i)   
            #logging.debug("Device %d: %s"%(i,devinfo["name"]))
            for keyword in ["mic","input"]:
                if keyword in devinfo["name"].lower():
                    #logging.debug("Found an input: device %d - %s"%(i,devinfo["name"]))
                    device_index = i
                    return device_index
        if device_index == None:
            logging.debug("No preferred input found; using default input device.")
        return device_index

    def open_mic_stream(self):
        stream = self.pa.open(format = self.audio_format,
                              channels = self.channels,
                              rate = self.rate,
                              input = True,
                              input_device_index = self.device_index,
                              frames_per_buffer = self.fpb)
        return stream

    def listen(self, rms_thresh, rec_thresh, write_thresh):
        try:
            block = self.stream.read(self.fpb, exception_on_overflow = False)
            amplitude = get_rms(block)
            print(amplitude)               
            if amplitude > rms_thresh and not self.recflag:
                self.rmscount += 1
                logging.debug("*--polling for sustained signal " + str(self.rmscount) + " / " + str(rec_thresh) + "--*")      
                if self.rmscount >= rec_thresh:
                    logging.info("*--recording initiated--*")
                    self.recflag = 1
                    self.rmscount = 0                  
            if amplitude < rms_thresh and not self.recflag:
                logging.debug("Resetting Listening Count")
                self.rmscount = 0        
            if self.recflag:
                self.rmscount += 1
                self.frames.append( block )
                logging.debug("*--block " + str(self.rmscount) + "/" + str(write_thresh) + "--*")                
            if self.rmscount > write_thresh:
                self.itercount += 1
                self.write_time = time.time()
                self.record_kill()
                self.postdata()
                self.rmscount = 0
                self.recflag = 0
        except IOError as e:
            self.errorcount += 1
            logging.error( "(%d) Error recording: %s"%(self.errorcount,e) )
    
    def postdata(self):
        fileindex = "/home/marek/Desktop/polyppi/recordings/" + self.write_base + str(self.write_time) + str(self.itercount) + ".wav"
        print(fileindex)
        if self.to_upload == True:
            file1 = self.drive.CreateFile({'parents': [{'id': self.upload_folder_id}]})
            file1.SetContentFile(fileindex)
            file1.Upload()
            logging.info("Recording Upload Complete")
            os.remove(fileindex)
        
    def record_kill(self):
        wf = wave.open("/home/marek/Desktop/polyppi/recordings/" + self.write_base + str(self.write_time) + str(self.itercount) + ".wav", 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.pa.get_sample_size(self.audio_format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(self.frames))
        wf.close()
        self.frames = []
        
    def is_streaming(self):
        if self.stream == None:
            return False
        if self.stream.is_active():
            return True
        return False    
        
        
class FilePlayback(object):
    def __init__(self):
        logging.info("Initializing Mixer")
        logging.info(alsaaudio.mixers())
        logging.info(alsaaudio.cards())
        logging.info(alsaaudio.pcms())
        for mixername in alsaaudio.mixers():
            logging.info("Trying " + str(mixername))
            if str(mixername) == "Master" or str(mixername) == "PCM":
                logging.info("Mixername" + str(mixername) + "selected")
                self.m = alsaaudio.Mixer(mixername)
        self.stream = None
        self.volume = None
        logging.info("Initialized File Player")
        
    def play(self, playdir, playback_volume):
        logging.info("Starting Playback")
        self.volume = playback_volume
        logging.info (self.volume)
        logging.info(self.m)
        self.m.setvolume(self.volume)
        logging.info("Selecting from " + str(playdir))
        playfile = playdir + "/" + random.choice(os.listdir(playdir))
        logging.info("Selected: " + str(playfile))
        self.wf = wave.open(playfile, 'rb')
        logging.info("Opened Playfile")
        self.pa = pyaudio.PyAudio()
        logging.info("Playing back " + playfile)
        self.stream = self.pa.open(format = self.pa.get_format_from_width(self.wf.getsampwidth()),
                              channels = self.wf.getnchannels(),
                              rate = self.wf.getframerate(),
                              output = True,
                              stream_callback = self.callback)
    
    def callback(self, in_data, frame_count, time_info, status):
        data = self.wf.readframes(frame_count)
        return(data, pyaudio.paContinue)
    
    def is_streaming(self):
        if self.stream == None:
            return False
        if self.stream.is_active():
            return True
        return False
    
    def killStream(self):
        logging.info ("Killing Playback Stream")
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()
    
    def fadeOut(self):
        if self.volume == None:
            return True
        if self.volume != 0:
            self.volume = self.volume - 5
            self.m.setvolume(self.volume)
            return False
        else:
            self.killStream()
            return True