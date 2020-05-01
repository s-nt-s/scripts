#!/bin/bash

P_ON=0
P_OFF=0
VPN=""

while [[ $# -gt 0 ]]; do
key="$1"
case $key in
    "on")
        P_ON=1
        shift
    ;;
    "off")
        P_OFF=1
        shift
    ;;
    *)
    if [ -z "$VPN" ]; then
        VPN="$1"
    else
        VPN="$VPN $1"
    fi
    shift
    ;;
esac
done

if [ -z "$VPN" ]; then
    VPN=$(nmcli con | grep " vpn " | cut -d' ' -f1 | head -n 1)
    if [ -z "$VPN" ]; then
        echo "VPN no encontrada"
        echo "$ nmcli con:"
        nmcli con
        exit 1
    fi
else
    if ! nmcli con | grep " vpn " | cut -d' ' -f1 | grep -q "$VPN"; then
        echo "VPN $VPN no encontrada"
        echo "$ nmcli con:"
        nmcli con
        exit 1
    fi
fi
ST=$(nmcli con | grep " vpn " | sed 's/  */ /g' | grep -E "^${VPN} " | cut -d' ' -f4)
if [ $P_ON -eq 1 ] && [ "$ST" != "--" ]; then
    exit 0
fi
if [ $P_OFF -eq 1 ] && [ "$ST" == "--" ]; then
    exit 0
fi
if [ "$ST" == "--" ]; then
    echo "$VPN off -> on"
    nmcli con up id "$VPN"
else
    echo "$VPN on -> off"
    nmcli con down id "$VPN"
fi
