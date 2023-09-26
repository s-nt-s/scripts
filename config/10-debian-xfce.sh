#!/bin/bash

cd "$(dirname "$0")"

sudo get  update
sudo get  -y install numix-gtk-theme
sudo apt install xfce4-whiskermenu-plugin


xfconf-query -c xfce4-session -np '/shutdown/ShowSuspend' -t 'bool' -s 'false'
xfconf-query -c xfce4-session -np '/shutdown/ShowHibernate' -t 'bool' -s 'false'
xfconf-query -c xfwm4 -p /general/mousewheel_rollup -s false
xfconf-query -c xfwm4 -p /general/workspace_count -s 1
xfconf-query -c xfwm4 -p /general/workspace_names -s "[1]" -s "[2]" -s "[3]" -s "[4]"
xfconf-query -c xfce4-panel -p /panels/panel-1/size -s 25
xfconf-query -c xfce4-session -np /compat/LaunchGNOME -t 'bool' -s 'true'
xfconf-query -c xfwm4 -p /general/use_compositing -s false
xfconf-query -c xfwm4 -p /general/wrap_windows -s false
xfconf-query -c xfwm4 -p /general/wrap_resistance -s 5
xfconf-query -c xfwm4 -p /general/button_layout -s 'O|HMC'
xfconf-query -c xfwm4 -p /general/box_resize -s true
xfconf-query -c xfwm4 -p /general/box_move -s true
xfconf-query -c xfwm4 -p /general/scroll_workspaces -s false
xfconf-query -c xfwm4 -p /general/cycle_draw_frame -s false

xfconf-query -c xsettings -p /Net/ThemeName -s Numix
xfconf-query -c xfwm4 -p /general/theme -s Numix
xfconf-query -c xsettings -p /Net/IconThemeName -s Mint-Y-Teal

sudo sed 's|^# es_ES.UTF-8|es_ES.UTF-8|' -i /etc/locale.gen
sudo locale-gen

