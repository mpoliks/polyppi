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
dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
playback_dir = dir_path + "/playback/"
playback_backup_dir = dir_path + "/playback_backup/"
recordings_dir = dir_path + "/recordings/"
logs_dir = dir_path + "/logs/"
log_file = logs_dir + "log.log"


class BootManager(object):

    def __init__(self):
        global status
        for dir in [playback_dir, playback_backup_dir, recordings_dir, logs_dir]:
            if not os.path.exists(dir):
                os.makedirs(dir)
        with open(log_file, "w"): pass
        logging.basicConfig(filename='logs/log.log', format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)
        self.wipe()
        logging.info("PID = " + str(os.getpid()))

    def wipe(self):
        logging.info("Wiping Recordings and Logs")
        try: 
            for f in os.listdir(recordings_dir):
                os.remove((os.path.join(recordings_dir, f)))
            with open(log_file, "w"): pass
        except OSError as e:
            logging.error( "(%d) Error wiping files: %s"%(e))
            
    def populate(self, drive, led):
        try:
            drive.file_download(download_folder, playback_dir)
            drive.backup_audio()
        except:
            logging.error("No GDrive Connection, Retoring Backups")
            drive.restore_backups()
        status = "ready"

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
        status = "holding"
    
    def pull_vitals(self, listener, player, battery):
        try:
            battery.vitals["charge_level"] = battery.charge_level()
        except IOError as e:
            logging.error ( "(%d) Error getting battery charge: %s"%(e))
        logging.info("VITALS: " + str(listener.vitals))
        logging.info("VITALS: " + str(player.vitals)) 
        logging.info("VITALS: " + str(battery.vitals))



class GDriveSetup(object):

    def __init__(self):
        logging.info("Initial Authorizing")
        self.gauth = GoogleAuth()
        self.authorize()
        logging.info("Accessing Google Drive")
        self.drive = GoogleDrive(self.gauth)
        self.pi_id = pi_id
        self.logs_dir = logs_dir
        
    def authorize(self):
        self.gauth.LoadCredentialsFile("cred.txt")
        if self.gauth.credentials is None:
            self.gauth.LocalWebserverAuth()
            logging.debug("No Credentials, Regrabbing")
        elif self.gauth.access_token_expired:
            self.gauth.Refresh()
            logging.debug("Access Token Expired")
        else:
            logging.debug("Authorizing")
            self.gauth.Authorize()
        self.gauth.SaveCredentialsFile("cred.txt")
        
    def file_download(self, folder_id, target_folder):
        file_list = self.drive.ListFile({'q': "'{}' in parents and trashed = false".format(folder_id)}).GetList()
        title_list = []
        for entry in file_list:
            title_list.append(entry['title'])
        to_download = set(title_list) - set(os.listdir(playback_dir))
        logging.info("Will Download the Files {}".format(to_download))
        to_remove = set(os.listdir(playback_dir)) - set(title_list)
        logging.info("Removing Old Files {}".format(to_remove))
        for i, entry in enumerate(file_list, start = 1):
            if entry['title'] in to_download:
                logging.info('Downloading {} from GDrive({}/{})'.format(entry['title'], i, len(to_download)))
                print('Downloading {} from GDrive({}/{})'.format(entry['title'], i, len(to_download)))
                entry.GetContentFile(entry['title'])
                os.rename((target_folder.replace("playback/", entry['title'])), (target_folder + entry['title']))
        for entry in os.listdir(playback_dir):
            if entry in to_remove:
                os.remove(os.path.join(playback_dir, entry))
        logging.info("Download Complete")
    
    def backup_audio(self):
        to_backup = set(os.listdir(playback_dir)) - set(os.listdir(playback_backup_dir))
        logging.info("Backing Up Files {}".format(to_backup))
        to_remove = set(os.listdir(playback_backup_dir)) - set(os.listdir(playback_dir))
        logging.info("Removing False Backups {}".format(to_remove))
        for entry in os.listdir(playback_dir):
            if entry in to_backup:
                shutil.move(os.path.join(playback_dir, entry), playback_backup_dir)
        for entry in os.listdir(playback_backup_dir):
            if entry in to_remove:
                os.remove(os.path.join(playback_backup_dir, entry))
                
    def restore_backups(self):
        if len(os.listdir(playback_dir)) > 2:
            logging.info("Electing Not To Backup; Playback Dir Has Content")
            return
        if len(os.listdir(playback_backup_dir)) < 1:
            logging.debug("Backup Dir Empty")
            return
        for f in os.listdir(playback_dir):
            os.remove((os.path.join(playback_dir, f)))
        for f in os.listdir(playback_backup_dir, f):
            shutil.move(os.path.join(playback_backup_dir, entry), playback_dir)
        logging.info("Restoring Backup")
        
    def upload_logs(self):
        fileindex = self.logs_dir + "/" + self.pi_id + str(datetime.now()) + ".log"
        os.rename (self.logs_dir + "/log.log", fileindex)
        logging.info("Uploading Logs")
        file1 = self.drive.CreateFile({'parents': [{'id': log_folder}]})
        file1.SetContentFile(fileindex)
        file1.Upload()
        logging.info("LogFile Upload Complete")
        os.remove(fileindex)
