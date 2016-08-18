#!/bin/bash

if [ ! -f ~/.bash_aliases ]; then
    cp mint.bash_aliases ~/.bash_aliases
	chmod 622 ~/.bash_aliases
fi

sudo apt-get update

# php5-mcrypt php5-curl && php5enmod mcrypt

# desintalar
sudo apt-get -y --purge remove xfburn totem banshee
#vim emacs emacs24 vim-tiny

# man
sudo apt-get -y install manpages-es manpages-es-extra
sudo dpkg-reconfigure locales

# temas
sudo apt-get -y install gnome-brave-icon-theme

# aplicaciones
sudo apt-get -y install virtualbox-nonfree chromium-browser filezilla keepassx calibre transgui chromium-browser-l10n mysql-workbench claws-mail claws-mail-extra-plugins claws-mail-i18n claws-mail-themes geany mkvtoolnix-gui gparted mumble pandoc system-config-samba

# eclipse eclipse-jdt eclipse-pde eclipse-platform eclipse-rcp

# icono de calibre
if [ -f /usr/share/calibre/images/viewer.png ]; then
	mkdir -p ~/.icons
	cp /usr/share/calibre/images/viewer.png ~/.icons/calibre.png
fi

if [ -f /usr/share/applications/defaults.list ]; then
	sudo sed 's/=\(totem\.desktop\|banshee-audiocd\.desktop\)/=vlc.desktop/' -i /usr/share/applications/defaults.list
fi

# gimp Ventanas -> singel mode

# sudo apt-get install mysql-server mysql-client

# /usr/share/polkit-1/actions/org.freedesktop.upower.policy
xfconf-query -c xfce4-session -np '/shutdown/ShowSuspend' -t 'bool' -s 'false'
xfconf-query -c xfce4-session -np '/shutdown/ShowHibernate' -t 'bool' -s 'false'
xfconf-query -c xfwm4 -p /general/mousewheel_rollup -s false
xfconf-query -c xfwm4 -p /general/workspace_count -s 2
xfconf-query -c xfwm4 -p /general/workspace_names -s "[1]" -s "[2]" -s "[3]" -s "[4]"
xfconf-query -c xfce4-panel -p /panels/panel-1/background-style -s 0
xfconf-query -c xfce4-session -p /compat/LaunchGNOME -s true
xfconf-query -c xfwm4 -p /general/use_compositing -s false
xfconf-query -c xfwm4 -p /general/wrap_windows -s false
xfconf-query -c xfwm4 -p /general/wrap_resistance -s 5
xfconf-query -c xfce4-notifyd -p /initial-opacity -s 1
xfconf-query -c xfce4-notifyd -p /notify-location -s 3
xfconf-query -c xsettings -p /Net/IconThemeName -s gnome-brave

# 1453923243: /plugins/plugin-3/sort-order (guint: 4)
# 1453923278: /plugins/plugin-3/middle-click (guint: 0)

