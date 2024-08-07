import requests
import json
import time
import sys
import logging

# Configuration
GCP_HOST = "34.66.128.13"
GCP_PORT = 5000
LOCAL_PATH = "/home/polyppi/raspberrypi-firmware/config.json"
LOG_FILE = "/var/log/sync_config.log"

# Configure logging
logging.basicConfig(filename=LOG_FILE, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger()

def send_discord_message(webhook_url, message):
    data = {"content": message}
    response = requests.post(webhook_url, json=data)
    if response.status_code != 204:
        logger.error(f"Failed to send message to Discord: {response.status_code}, {response.text}")
    else:
        logger.info(f"Successfully sent message to Discord: {message}")

def load_local_config():
    try:
        with open(LOCAL_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f'Configuration file not found: {LOCAL_PATH}')
        return {"MAX_VOLUME": 100}

def sync_config(webhook_url):
    url = f'http://{GCP_HOST}:{GCP_PORT}/get_config'
    try:
        logger.info(f"Fetching config from {url}")
        response = requests.get(url, timeout=10)  # Set a timeout
        if response.status_code == 200:
            config = response.json()
            logger.info(f"Received config: {config}")
            local_config = load_local_config()
            logger.info(f"Local config: {local_config}")
            if config.get('MAX_VOLUME') != local_config.get('MAX_VOLUME'):
                with open(LOCAL_PATH, 'w') as f:
                    json.dump(config, f, indent=4)
                logger.info(f"Config updated: {config}")
                send_discord_message(webhook_url, "Volume Change Received by Pi!")
            else:
                logger.info("No change in volume")
        else:
            logger.error(f"Failed to fetch config: {response.status_code}")
    except Exception as e:
        logger.error(f"Error: {e}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        logger.error("Usage: sync_config.py <discord_webhook_url>")
        sys.exit(1)

    webhook_url = sys.argv[1]

    while True:
        sync_config(webhook_url)
        time.sleep(20)  # Check for updates every 20 seconds
