FROM arm64v8/debian:buster-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y rsync cron ffmpeg python3-pip libasound2-dev alsa-utils openssh-client libportaudio2 libportaudiocpp0 portaudio19-dev && \
    pip3 install pydub numpy pyalsaaudio pyaudio

# Create .ssh directory
RUN mkdir -p /root/.ssh

# Copy known_hosts
COPY known_hosts /root/.ssh/known_hosts

# Copy scripts to the container
COPY audio_fw.py /usr/local/bin/audio_fw.py
COPY sync_to_gcp.sh /usr/local/bin/sync_to_gcp.sh
COPY startup.sh /usr/local/bin/startup.sh

# Set executable permissions
RUN chmod +x /usr/local/bin/audio_fw.py /usr/local/bin/sync_to_gcp.sh /usr/local/bin/startup.sh

# Set up cron job for syncing
RUN (crontab -l ; echo "0 0 * * * /usr/local/bin/sync_to_gcp.sh >> /var/log/sync.log 2>&1") | crontab -

# Start the startup script
CMD ["/usr/local/bin/startup.sh"]
