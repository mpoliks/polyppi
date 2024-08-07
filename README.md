This is some basic firmware with which to handle audio I/O through GCP.

Ensure you've cloned into ~/raspberrypi-firmware.

On a new build, move ssh keys to the known hosts subdir:
ssh-keyscan -H 34.66.128.13 >> ~/.ssh/known_hosts


Run:
docker build -t raspberrypi-firmware .
to build the Docker image.

To run the Docker image, use:
docker run -d --name raspberrypi-firmware --restart unless-stopped \
  --device /dev/snd \
  -v /home/polyppi/.ssh:/root/.ssh:ro \
  -v /home/polyppi/raspberrypi-firmware/synced_files:/home/polyppi/raspberrypi-firmware/synced_files \
  -v /home/polyppi/logs:/var/log \
  -e DISCORD_INIT_WEBHOOK=${add url here}"
  -e DISCORD_CRASH_WEBHOOK=${add url here}"
  -e DISCORD_HEARTBEAT_WEBHOOK=${add url here}"
  raspberrypi-firmware
docker exec -it raspberrypi-firmware /bin/bash

If you have a Docker image already running:
docker stop raspberrypi-firmware
docker rm raspberrypi-firmware

Use:
tail -f /var/log/audio_fw.log
to identify any logging issues.
