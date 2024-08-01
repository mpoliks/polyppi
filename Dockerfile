FROM arm64v8/debian:buster-slim

RUN apt-get update && \
    apt-get install -y rsync cron ffmpeg python3-pip libasound2-dev openssh-client alsa-utils

# Install required Python packages
RUN pip3 install pydub simpleaudio numpy pyalsaaudio

# Copy the scripts into the Docker image
COPY sync_to_gcp.sh /usr/local/bin/sync_to_gcp.sh
COPY volume_automation.py /usr/local/bin/volume_automation.py
COPY loop_audio.py /usr/local/bin/loop_audio.py

# Make the scripts executable
RUN chmod +x /usr/local/bin/sync_to_gcp.sh /usr/local/bin/volume_automation.py /usr/local/bin/loop_audio.py

# Add the cron job for sync script
RUN (crontab -l ; echo "@reboot /usr/local/bin/sync_to_gcp.sh") | crontab -
RUN (crontab -l ; echo "0 2 * * * /sbin/shutdown -r now") | crontab -

# Start cron and run the Python scripts in parallel
CMD ["bash", "-c", "cron && sleep 60 && python3 /usr/local/bin/volume_automation.py & sleep 120 && python3 /usr/local/bin/loop_audio.py & tail -f /dev/null"]
