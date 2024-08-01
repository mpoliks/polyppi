#!/bin/bash
mkdir -p /home/polyppi/raspberrypi-firmware/synced_files/
rsync -avz --progress --delete mpoliks@35.208.73.129:/home/mpoliks/synced_files/ /home/polyppi/raspberrypi-firmware/synced_files/
