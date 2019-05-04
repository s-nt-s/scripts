#!/bin/bash

if [ ! -f ~/.bash_aliases ]; then
    cp mint.bash_aliases ~/.bash_aliases
	chmod 622 ~/.bash_aliases
fi

sudo apt-get update

# man
sudo apt-get -y install manpages-es manpages-es-extra
sudo dpkg-reconfigure locales

# aplicaciones
sudo apt-get -y install virtualbox-nonfree chromium-browser filezilla keepassx calibre transgui chromium-browser-l10n mysql-workbench claws-mail claws-mail-extra-plugins claws-mail-i18n claws-mail-themes geany mkvtoolnix-gui gparted mumble pandoc system-config-samba claws-mail-pgpmime claws-mail-pgpcore hexchat-python3

