from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

class GDriveSetup(object):
    def __init__(self):
        
        self.gauth = GoogleAuth()
        self.authorize()
        self.drive = GoogleDrive(self.gauth)
        
    def authorize(self):
    
        self.gauth.LoadCredentialsFile("cred.txt")
        if self.gauth.credentials is None:
            self.gauth.LocalWebserverAuth()
        elif self.gauth.access_token_expired:
            self.gauth.Refresh()
        else:
            self.gauth.Authorize()
        self.gauth.SaveCredentialsFile("cred.txt")
        
    def file_download(self, folder_id):
        
        file_list = self.drive.ListFile({'q': "'{}' in parents and trashed = false".format(folder_id)}).GetList()
        for i, file1 in enumerate(sorted(file_list, key = lambda x: x['title']), start = 1):
            print('Downloading {} from GDrive({}/{})'.format(file1['title'], i, len(file_list)))
            file1.GetContentFile(file1['title'])
        print("Download Complete")
        
