This is some basic firmware with which to handle audio I/O through GCP.

Ensure you've cloned into home/usr.

On a new build, move ssh keys to the known hosts subdir:
ssh-keyscan -H {$host_ip}>> ~/.ssh/known_hosts

Run:
docker build -t raspberrypi-firmware .
to build the Docker image.

To run the Docker image, use:
docker run -d --name raspberrypi-firmware --restart unless-stopped \
  --device /dev/snd \
  -v $HOME/.ssh:/root/.ssh:ro \
  -v $HOME/raspberrypi-firmware/synced_files:$HOME/raspberrypi-firmware/synced_files \
  -v $HOME/raspberrypi-firmware/config.json:/app/config.json \
  -v $HOME/logs:/var/log \
  -e DISCORD_INIT_WEBHOOK="{url}" \
  -e DISCORD_CRASH_WEBHOOK="{url}" \
  -e DISCORD_HEARTBEAT_WEBHOOK="{url}" \
  raspberrypi-firmware

If you have a Docker image already running:
docker stop raspberrypi-firmware
docker rm raspberrypi-firmware

Use:
docker exec -it raspberrypi-firmware /bin/bash
tail -f /var/log/audio_fw.log
to identify any logging issues.
