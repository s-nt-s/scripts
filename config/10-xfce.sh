#!/bin/bash

sudo apt-get update

# temas
sudo apt-get -y install gnome-brave-icon-theme numix-gtk-theme

# icono de calibre
if [ -f /usr/share/calibre/images/viewer.png ]; then
	mkdir -p ~/.icons
	cp /usr/share/calibre/images/viewer.png ~/.icons/calibre.png
fi

# gimp Ventanas -> singel mode

xfconf-query -c xfce4-session -np '/shutdown/ShowSuspend' -t 'bool' -s 'false'
xfconf-query -c xfce4-session -np '/shutdown/ShowHibernate' -t 'bool' -s 'false'
xfconf-query -c xfwm4 -p /general/mousewheel_rollup -s false
xfconf-query -c xfwm4 -p /general/workspace_count -s 2
xfconf-query -c xfwm4 -p /general/workspace_names -s "[1]" -s "[2]" -s "[3]" -s "[4]"
xfconf-query -c xfce4-panel -p /panels/panel-1/background-style -s 0
xfconf-query -c xfce4-panel -p /panels/panel-1/size -s 25
xfconf-query -c xfce4-session -np /compat/LaunchGNOME -t 'bool' -s 'true'
xfconf-query -c xfwm4 -p /general/use_compositing -s false
xfconf-query -c xfwm4 -p /general/wrap_windows -s false
xfconf-query -c xfwm4 -p /general/wrap_resistance -s 5
xfconf-query -c xfwm4 -p /general/button_layout -s 'O|HMC'
xfconf-query -c xfwm4 -p /general/box_resize -s true
xfconf-query -c xfwm4 -p /general/box_move -s true
xfconf-query -c xfwm4 -p /general/scroll_workspaces -s false
xfconf-query -c xfce4-notifyd -p /initial-opacity -s 1
xfconf-query -c xfce4-notifyd -p /notify-location -s 3
xfconf-query -c xsettings -p /Net/IconThemeName -s gnome-brave
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/show-tray-icon -s 1
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/inactivity-sleep-mode-on-battery -s 1
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/inactivity-sleep-mode-on-ac -s 1
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/inactivity-on-battery -s 14
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/inactivity-on-ac -s 14
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/critical-power-action -s 3
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/dpms-enabled -s false
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/brightness-on-battery -s 9
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/brightness-on-ac -s 9
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/blank-on-battery -s 0
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/blank-on-ac -s 0
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/power-button-action -s 4
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/sleep-button-action -s 1
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/hibernate-button-action -s 0
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/lid-action-on-battery -s 1
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/lid-action-on-ac -s 0
xfconf-query -c xfce4-power-manager -p /xfce4-power-manager/logind-handle-lid-switch -s true


