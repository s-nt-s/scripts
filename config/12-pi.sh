#!/bin/bash

if [ -f "~/pi.pub" ]; then
	mkdir -p ~/.ssh
	chmod 700 ~/.ssh
	touch ~/.ssh/authorized_keys
	chmod 600 ~/.ssh/authorized_keys
	cat ~/pi.pub >> ~/.ssh/authorized_keys
	rm ~/pi.pub
fi

if [ ! -f ~/.bash_aliases ]; then
    cp pi.bash_aliases ~/.bash_aliases
	chmod 622 ~/.bash_aliases
fi

if [ ! -f ~/.netrc ]; then
	touch ~/.netrc
	chmod 600 ~/.netrc
fi

mkdir -p ~/dwn
mkdir -p ~/wks
mkdir -p ~/www
chmod 776 ~/dwn
sudo bash -c 'echo "" > /etc/motd'

sudo apt-get update
sudo systemctl disable apache2

sudo apt-get -y install sendxmpp fbi transmission-daemon omxplayer lynx fail2ban nginx telnet oracle-java8-jdk mkvtoolnix php5-cli php5-curl php5-mcrypt

sudo groupadd say
sudo adduser debian-transmission pi
sudo adduser debian-transmission say
sudo adduser pi debian-transmission

if [ -f /var/lib/transmission-daemon/info/settings.json ]; then
	sudo systemctl stop transmission-daemon
	sudo sed 's/"download-dir".*/"download-dir": "\/home\/pi\/dwn",/' -i /var/lib/transmission-daemon/info/settings.json
	sudo sed 's/"incomplete-dir".*/"incomplete-dir": "\/var\/lib\/transmission-daemon\/downloads",/' -i /var/lib/transmission-daemon/info/settings.json
	sudo sed 's/"incomplete-dir-enabled".*/"incomplete-dir-enabled": true,/' -i /var/lib/transmission-daemon/info/settings.json
	sudo sed 's/"script-torrent-done-enabled".*/"script-torrent-done-enabled": true,/' -i /var/lib/transmission-daemon/info/settings.json
	sudo sed 's/"script-torrent-done-filename".*/"script-torrent-done-filename": "\/home\/pi\/wks\/scripts\/complete.sh",/' -i /var/lib/transmission-daemon/info/settings.json
	sudo sed 's/"umask".*/"umask": 2,/' -i /var/lib/transmission-daemon/info/settings.json
	sudo systemctl start transmission-daemon
fi

sudo apt-get -y install exim4
sudo apt-get -y install sslh
sudo apt-get -y install mysql-server mysql-client

# Autologin
if [ !-f /etc/systemd/system/getty@tty1.service.d/autologin.conf ]; then
	echo "[Service]" > /tmp/autologin.conf
	echo "ExecStart=" >> /tmp/autologin.conf
	echo "ExecStart=-/sbin/agetty --autologin $(whoami) --noclear %I 38400 linux" >> /tmp/autologin.conf
	sudo chown root:root /tmp/autologin.conf
	sudo chmod 644 /tmp/autologin.conf
	sudo mkdir -pv /etc/systemd/system/getty@tty1.service.d
	sudo mv /tmp/autologin.conf /etc/systemd/system/getty@tty1.service.d/
fi
