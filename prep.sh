#!/bin/bash

cd "/home/pi/Desktop/polyppi"
rm -r "/home/pi/Desktop/polyppi/recordings"
rm -r "/home/pi/Desktop/polyppi/playback"
git fetch
mkdir "/home/pi/Desktop/polyppi/recordings"
mkdir "/home/pi/Desktop/polyppi/playback"