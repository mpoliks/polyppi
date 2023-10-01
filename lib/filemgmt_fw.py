from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
import os, shutil, logging, requests
from datetime import datetime

## GDrive Management
pi_id = "R3vE20"
download_folder = '101FNH6ERnutThe6ztVLF8U11UnT5fybD'
upload_folder = '1R8iCvcadFcgn3KGWdO_O4vAN-qa_YGig'
log_folder = '1_RQT4sVP3-KD6JX-G5wiDPwxYsPQ8y5O'

## Local File Management
dir_path = "/home/hydra/Desktop/polyppi"
playback_dir = dir_path + "/playback/"
playback_backup_dir = dir_path + "/playback_backup/"
recordings_dir = dir_path + "/recordings/"
logs_dir = dir_path + "/logs/"
log_file = logs_dir + "log.log"


class BootManager(object):

    def __init__(self):
        self.status = None
        global transition_flag
        self.schedule_flag = True
        
        logging.basicConfig(filename=log_file, format='%(asctime)s %(message)s', encoding='utf-8', level=logging.DEBUG)
        logging.info("PID = " + str(os.getpid()))
        
        for dir in [playback_dir, playback_backup_dir, recordings_dir, logs_dir]:
            if not os.path.exists(dir):
                os.makedirs(dir)
                logging.info("Made Dir {}".format(dir))
        with open(log_file, "w"): pass

        
    def check_internet(self, timeout):
        try:
            requests.head('http://www.google.com/', timeout=timeout)
            return True
        except requests.ConnectionError:
            return False
            
    def populate(self, drive, led):
        if self.schedule_flag == True:
            print("Populating Files")
            try:
                drive.file_download(download_folder, playback_dir)
                drive.backup_audio()
            except:
                logging.error("No GDrive Connection, Restoring Backups")
                drive.restore_backups()
                transition_flag = True
            self.schedule_flag = False
            self.status = "ready"
            print("Files Populated")

    def stall(self, listener, player):
        if self.schedule_flag == True:
            print("Stalling")
            if listener.is_streaming(): 
                logging.info("Pausing Listener")
                try: 
                    listener.stop()
                except IOError as e:
                    logging.error ( "(%d) Error stopping listener: %s"%(e))
            if player.is_streaming(): 
                logging.info("Pausing Player")
                try: player.killStream()
                except IOError as e:
                    logging.error ( "(%d) Error stopping listener: %s"%(e))
            self.schedule_flag = False
            self.status = "holding"
            logging.info("Succesfully Stalled")
            print("Stalled")
    
    def pull_vitals(self, listener, player, battery):
        if self.schedule_flag == True:
            print("Pulling Vitals")
            try:
                battery.vitals["charge_level"] = battery.charge_level()
            except IOError as e:
                logging.error ( "(%d) Error getting battery charge: %s"%(e))
            logging.info("VITALS: " + str(listener.vitals))
            logging.info("VITALS: " + str(player.vitals)) 
            logging.info("VITALS: " + str(battery.vitals))
            print("Pulled Vitals")
            self.schedule_flag = False
    
    def upload_logs(self, drive):
        if self.schedule_flag == True:
            print("Uploading Logs")
            drive.upload_logs()
            self.schedule_flag = False
    
    def reset(self):
        print("Resetting Flag")
        self.schedule_flag = True



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
                shutil.copyfile(os.path.join(playback_dir, entry), playback_backup_dir)
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
            shutil.copyfile(os.path.join(playback_backup_dir, entry), playback_dir)
        logging.info("Restoring Backup")
        
    def upload_logs(self):
        fileindex = self.logs_dir + "/" + self.pi_id + str(datetime.now()) + ".log"
        shutil.copyfile(log_file, fileindex)
        logging.info("Uploading Logs")
        try: 
            file1 = self.drive.CreateFile({'parents': [{'id': log_folder}]})
            file1.SetContentFile(fileindex)
            file1.Upload()
            logging.info("LogFile Upload Complete")
        except:
            logging.error("Internet Connection Timed Out")
        os.remove(fileindex)

