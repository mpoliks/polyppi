To install, run:

a) clone this repo to the pi somewhere accessible and navigate to that directory in your terminal (e.g. via `cd`).
b) run `pip install -r requirements.txt`
c) run `sudo chmox +x polyp.sh`
d) run `curl http://cdn.pisugar.com/release/pisugar-power-manager.sh | sudo bash`
e) run ifconfig and grab the local inet ip address
f) go to your browser and enter http://<your ip>:8421 and schedule wake up to "On Power Restore"
g) run `sudo nano /boot/config.txt`
h) add a "#" before the line `dtparam=audio=on`
i) change the vc4-mks overlay line to: `dtoverlay=vc4-kms-v3d,noaudio`
j) add the line `dtoverlay=hifiberry-dac`
k) uncomment the lines (remove the "#"):
	dtparam=i2c_arm=on
	dtparam=i2s=on
	dtparam=spi=on
l) write out the config file
m) run 'sudo touch /etc/asound.conf', 'sudo nano /etc/asound.conf' and add:
pcm.!default {
  type hw card 0
}
ctl.!default {
  type hw card 0
}
n) reboot (`sudo reboot`)
o) select `snd_rpi_hifiberrydac` as your output device and `Andrea Pure Audio` as your input device (in the menu bar the sound and mic icons)
p) troubleshoot here as needed: https://www.hifiberry.com/docs/software/configuring-linux-3-18-x/
q) run crontab -e and enter the lines "@reboot sh /home/marek/Desktop/polyppi/polyp.sh" at the bottom
r) reboot the pi (`sudo reboot`) and it will run, check log.log for any errors
