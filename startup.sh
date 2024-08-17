#!/bin/bash

# Log file
LOG_FILE="/var/log/startup.log"

echo "Starting startup script..." >> $LOG_FILE

# Start the audio firmware script
echo "Starting audio firmware script..." >> $LOG_FILE
python3 /usr/local/bin/audio_fw.py >> $LOG_FILE 2>&1 &
AUDIO_FW_PID=$!

if [ $? -eq 0 ]; then
    echo "[$(date)] Audio firmware script started with PID $AUDIO_FW_PID." >> $LOG_FILE
else
    echo "[$(date)] Failed to start audio firmware script." >> $LOG_FILE
    exit 1
fi

# Start the monitor script
echo "Starting monitor script..." >> $LOG_FILE
/usr/local/bin/monitor_docker.sh >> $LOG_FILE 2>&1 &
MONITOR_DOCKER_PID=$!

if [ $? -eq 0 ]; then
    echo "[$(date)] Monitor script started with PID $MONITOR_DOCKER_PID." >> $LOG_FILE
else
    echo "[$(date)] Failed to start monitor script." >> $LOG_FILE
    exit 1
fi

# Get the Discord webhook URL from the environment variable
WEBHOOK_URL=${DISCORD_HEARTBEAT_WEBHOOK}

# Start the sync config script
echo "Starting sync config script..." >> $LOG_FILE
python3 /usr/local/bin/sync_config.py "$WEBHOOK_URL" >> $LOG_FILE 2>&1 &
SYNC_CONFIG_PID=$!

if [ $? -eq 0 ]; then
    echo "[$(date)] Sync config script started with PID $SYNC_CONFIG_PID." >> $LOG_FILE
else
    echo "[$(date)] Failed to start sync config script." >> $LOG_FILE
    exit 1
fi
# Keep the script running to avoid container exit
wait $AUDIO_FW_PID
wait $MONITOR_DOCKER_PID
wait $SYNC_CONFIG_PID
