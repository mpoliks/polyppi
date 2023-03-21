To install, run:

a) clone this repo to the pi somewhere accessible and navigate to that directory in your terminal (e.g. via `cd`).
b) run `pip install -r requirements.txt`
c) run `sudo chmox +x polyp.sh`
d) run `curl http://cdn.pisugar.com/release/pisugar-power-manager.sh | sudo bash`
e) run ifconfig and grab the local inet ip address
f) go to your browser and enter http://<your ip>:8421 and schedule wake up to "On Power Restore"
g) run crontab -e and enter the lines "@reboot sh /home/marek/Desktop/polyppi/polyp.sh" at the bottom
h) run `sudo nano /boot/config.txt`
i) add a "#" before the line `dtparam=audio=on`
j) change the vc4-mks overlay line to: `dtoverlay=vc4-kms-v3d,noaudio`
k) add the line `dtoverlay=hifiberry-dac`
l) uncomment the lines (remove the "#"):
	dtparam=i2c_arm=on
	dtparam=i2s=on
	dtparam=spi=on
m) write out the config file
n) select `snd_rpi_hifiberrydac` as your output device and `Andrea Pure Audio` as your input device (in the menu bar the sound and mic icons)
n) reboot the pi (`sudo reboot`) and it will run, check log.log for any errors
