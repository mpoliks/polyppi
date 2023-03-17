import pyaudio
import wave
import math
import struct
import alsaaudio
import time
import random
import os

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
    def __init__(self, channels, rate, fpb, write_base, drive, drive_loc, to_upload):
        print("OK: Listener Initialized")
        self.frames = []
        self.itercount = 0        
        self.recflag = 0
        self.rmscount = 0
        self.errorcount = 0        
        self.audio_format = pyaudio.paInt16
        self.channels = channels
        self.rate = rate
        self.fpb = fpb
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
            print( "(%d) Error pausing stream: %s"%(self.errorcount,e) )
        
    def start(self):
        self.stream = self.open_mic_stream()

    def find_input_device(self):
        device_index = None            
        for i in range( self.pa.get_device_count() ):     
            devinfo = self.pa.get_device_info_by_index(i)   
            print("Device %d: %s"%(i,devinfo["name"]))
            for keyword in ["mic","input"]:
                if keyword in devinfo["name"].lower():
                    print( "Found an input: device %d - %s"%(i,devinfo["name"]) )
                    device_index = i
                    return device_index
        if device_index == None:
            print( "No preferred input found; using default input device." )
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
        except IOError as e:
            self.errorcount += 1
            print( "(%d) Error recording: %s"%(self.errorcount,e) )
        amplitude = get_rms(block)
        print(amplitude)               
        if amplitude > rms_thresh and not self.recflag:
            self.rmscount += 1
            print("OK: *--polling for sustained signal " + str(self.rmscount) + " / " + str(rec_thresh) + "--*")      
            if self.rmscount >= rec_thresh:
                print("OK: *--recording initiated--*")
                self.recflag = 1
                self.rmscount = 0                  
        if amplitude < rms_thresh and not self.recflag:
            print("OK: Resetting Listening Count")
            self.rmscount = 0        
        if self.recflag:
            self.rmscount += 1
            self.frames.append( block )
            presence_thresh = True
            print("OK: *--block " + str(self.rmscount) + "/" + str(write_thresh) + "--*")                
        if self.rmscount > write_thresh:
            self.itercount += 1
            self.write_time = time.time()
            self.record_kill()
            self.postdata()
            self.rmscount = 0
            self.recflag = 0
    
    def postdata(self):
        fileindex = "/home/marek/Desktop/polyppi/recordings/" + self.write_base + str(self.write_time) + str(self.itercount) + ".wav"
        print(fileindex)
        if self.to_upload == True:
            file1 = self.drive.CreateFile({'parents': [{'id': self.upload_folder_id}]})
            file1.SetContentFile(fileindex)
            file1.Upload()
        
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
        print("OK: Initialized File Player")
        self.m = alsaaudio.Mixer()
        self.stream = None
        
    def play(self, playdir, playback_volume):
        print("OK: Starting Playback")
        self.volume = playback_volume
        self.m.setvolume(self.volume)
        playfile = playdir + "/" + random.choice(os.listdir(playdir))
        self.wf = wave.open(playfile, 'rb')
        self.pa = pyaudio.PyAudio()
        print("OK: Playing back " + playfile)
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
        print ("OK: Killing Stream")
        self.stream.stop_stream()
        self.stream.close()
        self.pa.terminate()
    
    def fadeOut(self):
        if self.volume != 0:
            self.volume = self.volume - 5
            self.m.setvolume(self.volume)
            return
        self.killStream()