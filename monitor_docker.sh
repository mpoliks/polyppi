#!/bin/bash

LOG_FILE="/var/log/monitor_docker.log"
STARTUP_LOG_FILE="/var/log/startup.log"
CONTAINER_NAME="audio_firmware"
DISCORD_CRASH_WEBHOOK=$DISCORD_CRASH_WEBHOOK

# Function to send a message to Discord
send_discord_message() {
  local webhook_url=$1
  local message=$2
  curl -H "Content-Type: application/json" -X POST -d "{\"content\": \"$message\"}" $webhook_url >> $LOG_FILE 2>&1
}

# Function to send the last few lines of the startup log to Discord
send_startup_log_to_discord() {
  local webhook_url=$1
  local log_lines
  log_lines=$(tail -n 10 $STARTUP_LOG_FILE)
  local message="Container crashed or halted on $(hostname) by $(whoami). Last 10 lines of startup log:\n$log_lines"
  send_discord_message $webhook_url "$message"
}

# Monitor the script logs
while true; do
  if ! pgrep -f /usr/local/bin/audio_fw.py > /dev/null; then
    send_startup_log_to_discord $DISCORD_CRASH_WEBHOOK
    echo "Restarting audio_fw.py script..." >> $LOG_FILE
    python3 /usr/local/bin/audio_fw.py >> $LOG_FILE 2>&1 &
  fi
  sleep 20
done
