import os
import schedule
import time
import subprocess
import requests
import logging

# Configure logging
logging.basicConfig(filename='/var/log/sync_scheduler.log', level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger()

DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

def send_discord_message(message):
    if DISCORD_WEBHOOK_URL:
        data = {"content": message}
        try:
            response = requests.post(DISCORD_WEBHOOK_URL, json=data)
            if response.status_code == 204:
                logger.info(f"Successfully sent message to Discord: {message}")
            else:
                logger.error(f"Failed to send message to Discord: {response.status_code}, {response.text}")
        except Exception as e:
            logger.error(f"Error sending message to Discord: {str(e)}")
    else:
        logger.warning("DISCORD_WEBHOOK_URL not set, skipping Discord notification")

def sync_to_gcp():
    logger.info("Starting sync_to_gcp.sh script")
    result = subprocess.run(['/usr/local/bin/sync_to_gcp.sh'], capture_output=True, text=True)
    if result.returncode == 0:
        logger.info("sync_to_gcp.sh completed successfully")
        send_discord_message("Sync to GCP completed successfully.")
    else:
        logger.error(f"sync_to_gcp.sh failed with return code {result.returncode}")
        logger.error(result.stderr)
        send_discord_message("Sync to GCP failed.")

# Schedule the sync job to run every hour
schedule.every().hour.do(sync_to_gcp)

logger.info("Sync scheduler started, sync job scheduled every hour")

while True:
    schedule.run_pending()
    time.sleep(1)
