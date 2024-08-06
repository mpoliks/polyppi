#!/bin/bash

# Log file
LOG_FILE="/var/log/sync.log"

# Sync with GCP on reboot
echo "Syncing with GCP..." >> $LOG_FILE
/usr/local/bin/sync_to_gcp.sh >> $LOG_FILE 2>&1

# Check if the sync was successful
if [ $? -eq 0 ]; then
    echo "GCP sync completed successfully." >> $LOG_FILE
else
    echo "GCP sync failed." >> $LOG_FILE
    exit 1
fi

# Start the audio firmware script
echo "Starting audio firmware script..." >> $LOG_FILE
python3 /usr/local/bin/audio_fw.py >> $LOG_FILE 2>&1

echo "[$(date)] Audio firmware script started." >> $LOG_FILE
