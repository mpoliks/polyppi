This is some basic firmware with which to handle audio I/O through GCP.

To install:

ssh-keygen -t ed25519 -C "mpoliks@gmail.com"

eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519

cat ~/.ssh/id_ed25519.pub

—> Github
—> GCP

git clone git@github.com:mpoliks/polyppi.git

mv ~/polyppi ~/raspberrypi-firmware


cd raspberrypi-firmware
mkdir synced_files

cd synced_files
mkdir epflsync

cd ..

sudo apt-get update
sudo apt-get upgrade -y

curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

sudo usermod -aG docker $USER
  
sudo reboot

cd ~/raspberrypi-firmware


ssh-keyscan -H 34.66.128.13 > known_hosts

rsync -avz --progress --delete -e "ssh -i ~/.ssh/id_ed25519" mpoliks@34.66.128.13:/home/mpoliks/synced_files/ ~/raspberrypi-firmware/synced_files/

EDIT:
- audio_fw.py (3x)
- sync_config.py (1x)
- Dockerfile (1)


docker build -t raspberrypi-firmware .

EDIT CMD BELOW:
To run the Docker image, use:
docker run -d --name raspberrypi-firmware --restart unless-stopped \
  --device /dev/snd \
  -v /home/polyp3/.ssh:/root/.ssh:ro \
  -v /home/polyp3/raspberrypi-firmware/synced_files:/home/polyp3/raspberrypi-firmware/synced_files \
  -v /home/polyp3/raspberrypi-firmware/config.json:/home/polyp3/raspberrypi-firmware/config.json \
  -v /home/polyp3/logs:/var/log \
  -e DISCORD_INIT_WEBHOOK="https://discord.com/api/webhooks/1270545026887454841/8l9XEDmoYboZWoZ-8FXL8fPtvJjVp4rcFhlrYxQefqbvl4Lyf_0Gja-ATZDdpPiYwpQ6" \
  -e DISCORD_CRASH_WEBHOOK="https://discord.com/api/webhooks/1270545026887454841/8l9XEDmoYboZWoZ-8FXL8fPtvJjVp4rcFhlrYxQefqbvl4Lyf_0Gja-ATZDdpPiYwpQ6" \
  -e DISCORD_HEARTBEAT_WEBHOOK="https://discord.com/api/webhooks/1270545026887454841/8l9XEDmoYboZWoZ-8FXL8fPtvJjVp4rcFhlrYxQefqbvl4Lyf_0Gja-ATZDdpPiYwpQ6" \
  raspberrypi-firmware

If you have a Docker image already running:
docker stop raspberrypi-firmware
docker rm raspberrypi-firmware

Use:
docker exec -it raspberrypi-firmware /bin/bash
tail -f /var/log/audio_fw.log
to identify any logging issues.

