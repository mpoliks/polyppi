import pyaudio, wave, alsaaudio
from pydub import AudioSegment, effects  
import math, struct, time, datetime, random
from statistics import mean
import os, logging


## Audio Settings
channels = 1
sample_rate = 48000
block_freq = 0.5 #frequency of input monitor
frames_per_block = int(sample_rate*block_freq)
rms_thresh = 0.01 #amp threshold over which presence is determined
playback_volume = 90 #volume in % of playback
dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
playback_dir = dir_path + "/playback"


class RMSListener(object):
    def __init__(self):
        logging.info("Listener Initialized")
        self.frames = []
        self.readings = []
        self.rmscount = 0
        self.rampcount = 0
        self.ramping = "Waiting"
        self.errorcount = 0    
        self.volume = 0  
        self.audio_format = pyaudio.paInt16
        self.channels = channels
        self.rate = sample_rate
        self.fpb = frames_per_block
        self.rms_thresh = rms_thresh   
        self.pa = pyaudio.PyAudio()
        self.device_index = self.find_input_device()
        self.initialize_mixer()
        self.start()
        
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

    def initialize_mixer(self):
        logging.info("Initializing Mixer")
        logging.info(alsaaudio.mixers())
        logging.info(alsaaudio.cards())
        logging.info(alsaaudio.pcms())
        for mixername in alsaaudio.mixers():
            logging.info("Trying " + str(mixername))
            if str(mixername) == "Master" or str(mixername) == "PCM":
                logging.info("Mixername" + str(mixername) + "selected")
                self.m = alsaaudio.Mixer(mixername)
        
    def stop(self):
        try:
            self.stream.close()
        except IOError as e:
            self.errorcount += 1
            logging.error( "(%d) Error pausing stream: %s"%(self.errorcount,e) )
        
    def start(self):
        self.stream = self.open_mic_stream()
            
    def get_rms(self, block):
        count = len(block)/2
        format = "%dh"%(count)
        shorts = struct.unpack(format, block )
        sum_squares = 0.0
        for sample in shorts:
            n = sample * (1.0/32768.0)
            sum_squares += n*n
        return math.sqrt(sum_squares / count)

    def calibrate_rms(self, new_reading):
        self.readings.append(new_reading)        
        if len(self.readings) < 5:
            return self.rms_thresh
        if len(self.readings) >= 20:
            self.readings.pop(0)
        return mean(self.readings) * 1.6

    def listen(self):
        try:
            block = self.stream.read(self.fpb, exception_on_overflow = False)
            amplitude = self.get_rms(block)
            #print(amplitude)                
            self.rms_thresh = self.calibrate_rms(amplitude)
        except IOError as e:
            self.errorcount += 1
        if self.ramping != "Waiting":
            self.ramp()
            return "triggered"
        if amplitude > self.rms_thresh: self.rmscount += 1
        if amplitude < self.rms_thresh: self.rmscount = 0
        if self.rmscount > 3: 
            self.ramping = "Fadein"
            logging.info("Event Detected, Fading In")
            self.ramp()   
            return "triggered"     
        return "inert"
            
    def ramp(self):
        if self.ramping == "Fadein": 
            if self.volume < 90: self.volume += 3
            if self.volume >= 90: 
                self.ramping = "Fadeout"
                logging.info("Fading Out")
        if self.ramping == "Fadeout":
            if self.volume > 10: self.volume -= 1
            if self.volume <= 10: 
                self.ramping = "Waiting"
                self.rmscount = 0
        self.m.setvolume(self.volume)
        
        
    def is_streaming(self):
        if self.stream == None:
            return False
        if self.stream.is_active():
            return True
        return False   
        
        
class FilePlayback(object):
    def __init__(self):
        logging.info("Initialized File Player")
        self.play()
        
    def play(self):
        logging.info("Starting Playback")
        vari = "/origin"
        
        if datetime.datetime.now().month == 10:
            if datetime.datetime.now().day >= 25:
                vari = "/first"
        
        if datetime.datetime.now().month == 11:
            if datetime.datetime.now().day < 6:
                vari = "/first"
            if datetime.datetime.now().day >= 6:
                vari = "/second"
            if datetime.datetime.now().day >= 20:
                vari = "/third"
                
        if datetime.datetime.now().month == 12:
            if datetime.datetime.now().day <= 27:
                vari = "/third"
            if datetime.datetime.now().day > 27:
                vari = "/fourth"
            
        if datetime.datetime.now().month < 10:
                vari = "/fourth"
                
        logging.info("Selecting from " + str(playback_dir) + vari)
        playfile = playback_dir + vari +"/" + random.choice(os.listdir(playback_dir + vari))
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
        
    def loop(self):
        if self.is_streaming() == False:
            logging.info("Looping")
            self.killStream()
            self.play()

    def killStream(self):
        logging.info ("Killing Playback Stream")
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()
    
    def is_streaming(self):
        try:
            if self.stream == None: return False
            if self.stream.is_active(): return True
        except OSError as e:
            return False
        return False
        




        
    
    
