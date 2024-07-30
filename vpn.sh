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

vpn_command() {
    LANG=en_US.UTF-8 nmcli -t -f NAME,TYPE,TIMESTAMP-REAL connection show | \
    grep ':vpn:' | \
    while IFS=: read -r name type timestamp; do
        tm=$(echo "$timestamp" | sed 's|\\||g')
        epoch=$(date -d "$tm" +%s)
        echo "$epoch:$name"
    done | \
    sort -t ':' -k1 -r | \
    cut -d ':' -f2-
}

declare -a VPNS

while IFS= read -r line; do
    VPNS+=("$line")
done < <(vpn_command)

if [ ${#VPNS[@]} -eq 0 ]; then
    echo "No hay VPNs"
    exit 1
fi

if [ -z "$VPN" ]; then
    VPN="${VPNS[0]}"
elif ! echo "${VPNS[@]}" | grep -q -F "$VPN"; then
    VPN=""
fi

if [ -z "$VPN" ]; then
    echo "VPN no encontrada"
    echo "VPNs disponibles:"
    for v in "${VPNS[@]}"; do
        echo "  $v"
    done
    exit 1
fi

DVC=$(nmcli -t -f DEVICE,TYPE,NAME connection show | grep -E ":vpn:${VPN}$" | cut -d':' -f1)
if [ $P_ON -eq 1 ] && [ ! -z "$DVC" ]; then
    exit 0
fi
if [ $P_OFF -eq 1 ] && [ -z "$DVC" ]; then
    exit 0
fi
if [ -z "$DVC" ]; then
    echo "$VPN off -> on"
    nmcli con up id "$VPN"
else
    echo "$VPN on -> off"
    nmcli con down id "$VPN"
fi
