#!/bin/bash

cd "/home/marek/Desktop/polyppi"
rm -r "/home/marek/Desktop/polyppi/recordings"
rm -r "/home/marek/Desktop/polyppi/playback"
mkdir "/home/marek/Desktop/polyppi/recordings"
mkdir "/home/marek/Desktop/polyppi/playback"
python3 "/home/marek/Desktop/polyppi/statemachine.py"