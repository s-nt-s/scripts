#!/bin/bash

cd "$(dirname "$0")"

if [ ! -f ~/.config/autostart/mintwelcome.desktop ]; then
if [ -f /etc/xdg/autostart/mintwelcome.desktop ]; then
    cp rec/mintwelcome.desktop ~/.config/autostart/mintwelcome.desktop
fi
fi

xfconf-query -c xfce4-session -np '/shutdown/ShowSuspend' -t 'bool' -s 'false'
xfconf-query -c xfce4-session -np '/shutdown/ShowHibernate' -t 'bool' -s 'false'
xfconf-query -c xfwm4 -p /general/mousewheel_rollup -s false
xfconf-query -c xfwm4 -p /general/workspace_count -s 1
xfconf-query -c xfwm4 -p /general/workspace_names -s "[1]" -s "[2]" -s "[3]" -s "[4]"
xfconf-query -c xfce4-panel -p /panels/panel-1/background-style -s 0
xfconf-query -c xfce4-panel -p /panels/panel-1/size -s 25
# xfconf-query -c xfce4-panel -p /plugins/plugin-6/sort-order -s 4
# xfconf-query -c xfce4-panel -p /plugins/plugin-6/window-scrolling -s false
xfconf-query -c xfce4-session -np /compat/LaunchGNOME -t 'bool' -s 'true'
xfconf-query -c xfwm4 -p /general/use_compositing -s false
xfconf-query -c xfwm4 -p /general/wrap_windows -s false
xfconf-query -c xfwm4 -p /general/wrap_resistance -s 5
xfconf-query -c xfwm4 -p /general/button_layout -s 'O|HMC'
xfconf-query -c xfwm4 -p /general/box_resize -s true
xfconf-query -c xfwm4 -p /general/box_move -s true
xfconf-query -c xfwm4 -p /general/scroll_workspaces -s false
xfconf-query -c xfwm4 -p /general/cycle_draw_frame -s false
xfconf-query -c xfce4-notifyd -p /initial-opacity -s 1
xfconf-query -c xfce4-notifyd -p /notify-location -s 3
xfconf-query -c xfce4-desktop -p /desktop-icons/show-tooltips -t 'bool' -s 'false'
xfconf-query -c xfce4-desktop -p /desktop-icons/file-icons/show-removable -t 'bool' -s 'false'
xfconf-query -c xfce4-desktop -p /desktop-icons/file-icons/show-trash -t 'bool' -s 'true'
xfconf-query -c xfce4-desktop -p /desktop-icons/file-icons/show-home -t 'bool' -s 'false'

#sudo apt-get update
#temas
#sudo apt-get -y install numix-gtk-theme
#if [ ! -f ~/.config/gtk-3.0/gtk.css ]; then
#    cp rec/gtk.css  ~/.config/gtk-3.0/gtk.css
#fi
#xfconf-query -c xsettings -p /Net/ThemeName -s Numix
#xfconf-query -c xsettings -p /Net/IconThemeName -s Mint-Y-Teal
#xfconf-query -c xfwm4 -p /general/theme -s Numix
