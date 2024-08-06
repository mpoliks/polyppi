#!/bin/bash

# Variables
GCP_USER="mpoliks"
GCP_HOST="34.66.128.13"
GCP_PATH="/home/mpoliks/synced_files/"
LOCAL_PATH="/home/polyppi/raspberrypi-firmware/synced_files/"

# Sync with GCP
mkdir -p $LOCAL_PATH
rsync -avz --progress --delete -e "ssh -i ~/.ssh/id_rsa" $GCP_USER@$GCP_HOST:$GCP_PATH $LOCAL_PATH
