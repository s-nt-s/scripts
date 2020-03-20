#!/bin/bash

VPN=$(nmcli con | grep " vpn " | cut -d' ' -f1)
if [ -z "$VPN" ]; then
    echo "VPN no encontrada. nmcli con:"
    nmcli con
    exit 1
fi
ST=$(nmcli con | grep " vpn " | sed 's/  */ /g' | cut -d' ' -f4)
if [ "$ST" == "--" ]; then
    echo "$VPN off -> on"
    nmcli con up id "$VPN"
else
    echo "$VPN on -> off"
    nmcli con down id "$VPN"
fi
