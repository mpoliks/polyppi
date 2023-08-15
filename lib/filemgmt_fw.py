from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os, shutil, logging
from datetime import datetime

## GDrive Management
pi_id = "R3vE20"
download_folder = '101FNH6ERnutThe6ztVLF8U11UnT5fybD'
upload_folder = '1R8iCvcadFcgn3KGWdO_O4vAN-qa_YGig'
log_folder = '1_RQT4sVP3-KD6JX-G5wiDPwxYsPQ8y5O'

## Local File Management
dir_path = os.path.dirname(os.path.realpath(__file__))
playback_dir = dir_path + "/playback/"
playback__backup_dir = dir_path + "/playback_backup/"
recordings_dir = dir_path + "/recordings/"
logs_dir = dir_path + "/logs/"
log_file = logs_dir + "logs/log.log"


class BootManager(object):

    def __init__(self):
        for dir in [playback_dir, playback__backup_dir, recordings_dir, logs_dir]:
            if not os.path.exists(dir):
                os.makedirs(dir)
        with open(log_file, "w"): pass
        logging.basicConfig(filename='logs/log.log', format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)
        logging.info("PID = " + str(os.getpid()))

    def wipe(self, drive, led):
        logging.log("Wiping Everything")
        try: 
            for f in os.listdir(playback_dir):
                os.remove(os.path.join(dir, f))
            for f in os.listdir(recordings_dir):
                os.remove(os.path.join(dir, f))
            with open(log_file, "w"): pass
        except OSError as e:
            logging.error( "(%d) Error wiping files: %s"%(e))
        try: 
            logging.log("Downloading Files")
            drive.file_download(download_folder, playback_dir)
            logging.log("Transferring Backups")
            for f in os.listdir(playback__backup_dir):
                os.remove(os.path.join(dir, f))
            shutil.copytree(playback_dir, playback__backup_dir)         
        except: 
            logging.error("No GDrive Connection")
            test_mode = True
            led.status("err")
            shutil.copytree(playback__backup_dir, playback_dir)
            logging.error("Restoring Base Playback Files")
        return "ready"

    def stall(self, listener, player):
        if listener.is_streaming(): 
            try: 
                listener.stop()
            except IOError as e:
                logging.error ( "(%d) Error stopping listener: %s"%(e))
        if player.is_streaming(): 
            try: player.killStream()
            except IOError as e:
                logging.error ( "(%d) Error stopping listener: %s"%(e))
        return "holding"
    
    def pull_vitals(self, listener, player, battery):
        try:
            battery.vitals["charge_level"] = battery.charge_level()
        except IOError as e:
            logging.error ( "(%d) Error getting battery charge: %s"%(e))
        logging.info("VITALS: " + str(listener.vitals))
        logging.info("VITALS: " + str(player.vitals)) 
        logging.info("VITALS: " + str(battery.vitals))



class GDriveSetup(object):

    def __init__(self, pi_id, logs_dir):
        self.gauth = GoogleAuth()
        self.authorize()
        self.drive = GoogleDrive(self.gauth)
        self.pi_id = pi_id
        self.logs_dir = logs_dir
        
    def authorize(self):
        self.gauth.LoadCredentialsFile("cred.txt")
        if self.gauth.credentials is None:
            self.gauth.LocalWebserverAuth()
        elif self.gauth.access_token_expired:
            self.gauth.Refresh()
        else:
            self.gauth.Authorize()
        self.gauth.SaveCredentialsFile("cred.txt")
        
    def file_download(self, folder_id, target_folder):
        file_list = self.drive.ListFile({'q': "'{}' in parents and trashed = false".format(folder_id)}).GetList()
        for i, file1 in enumerate(sorted(file_list, key = lambda x: x['title']), start = 1):
            logging.info('Downloading {} from GDrive({}/{})'.format(file1['title'], i, len(file_list)))
            file1.GetContentFile(file1['title'])
            os.rename((target_folder.replace("playback/", file1['title'])), (target_folder + file1['title']))
        logging.info("Download Complete")

    def upload_logs(self):
        fileindex = self.logs_dir + "/" + self.pi_id + str(datetime.now()) + ".log"
        os.rename (self.logs_dir + "/log.log", fileindex)
        print(fileindex)
        file1 = self.drive.CreateFile({'parents': [{'id': log_folder}]})
        file1.SetContentFile(fileindex)
        file1.Upload()
        logging.info("LogFile Upload Complete")
        os.remove(fileindex)