import requests
import json
import time

GCP_USER = "mpoliks"
GCP_HOST = "34.66.128.13"
GCP_PATH = "/home/mpoliks/config.json"
GCP_PORT = 5000
LOCAL_PATH = "/home/polyppi/raspberrypi-firmware/config.json"

def sync_config():
    url = f'http://{GCP_HOST}:{GCP_PORT}/get_config'
    try:
        response = requests.get(url)
        if response.status_code == 200:
            config = response.json()
            with open(LOCAL_PATH, 'w') as f:
                json.dump(config, f, indent=4)
            print(f"Config updated: {config}")
        else:
            print(f"Failed to fetch config: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    while True:
        sync_config()
        time.sleep(20)  # Check for updates every 20 seconds
