FROM arm64v8/debian:buster-slim

# Install dependencies
RUN apt-get update && \
    apt-get install -y rsync cron ffmpeg python3-pip libasound2-dev alsa-utils portaudio19-dev && \
    pip3 install pydub numpy pyalsaaudio pyaudio

# Copy scripts to the container
COPY audio_fw.py /usr/local/bin/audio_fw.py
COPY sync_to_gcp.sh /usr/local/bin/sync_to_gcp.sh

# Set executable permissions
RUN chmod +x /usr/local/bin/audio_fw.py /usr/local/bin/sync_to_gcp.sh

# Set up cron job for syncing
RUN (crontab -l ; echo "0 0 * * * /usr/local/bin/sync_to_gcp.sh") | crontab -

# Start the audio firmware script
CMD ["python3", "/usr/local/bin/audio_fw.py"]
