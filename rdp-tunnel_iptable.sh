#!/bin/bash

# SOURCE: https://kgibran.wordpress.com/2019/03/13/remmina-rdp-ssh-tunnel-with-pre-and-post-scripts/

scriptname="$(basename $0)"

if [ $# -lt 3 ]; then
    echo "Usage: $scriptname start | stop SSH_TUNNEL IP:PORT"
    exit
fi

exe() {
  CM=$(echo "$@" | sed "s|${HOME}/|~/|g")
  echo "\$ $CM"
  "$@"
}

SSH_TUNNEL="$2"
RDP_IPPORT="$3"

if [[ "$RDP_IPPORT" != *":"* ]]; then
  RDP_IPPORT="$RDP_IPPORT:3389"
fi
RDP_IP=$(echo "$RDP_IPPORT" | sed 's/:.*//')
RDP_PORT=$(echo "$RDP_IPPORT" | sed 's/.*://')

if [[ "$SSH_TUNNEL" != *":"* ]]; then
    SSH_NAME="$SSH_TUNNEL"
    SSH_PORT=$(md5sum <<< "$RDP_IPPORT")
    SSH_PORT=$((0x${SSH_PORT%% *}))
    SSH_PORT=$(($SSH_PORT % 16383))
    SSH_PORT=$((49152+SSH_PORT))
else
    SSH_NAME=$(echo "$SSH_TUNNEL" | sed 's/:.*//')
    SSH_PORT=$(echo "$SSH_TUNNEL" | sed 's/.*://')
fi

CRL="/tmp/ssh_${scriptname}_${SSH_TUNNEL}_${RDP_IPPORT}.control"

case "$1" in

start)
  echo "Starting tunnel to $SSH_TUNNEL"
  exe sudo iptables -t nat -A OUTPUT -p tcp -d "${RDP_IP}" --dport "${RDP_PORT}" -j DNAT --to-destination "127.0.0.1:${SSH_PORT}"
  exe ssh -M -S "$CRL" -fnNT -L "${SSH_PORT}:${RDP_IPPORT}" "$SSH_NAME"
  exe ssh -S "$CRL" -O check "$RDP_IP"
  ;;

stop)
  echo "Stopping tunnel to $SSH_TUNNEL"
  exe ssh -S "$CRL" -O exit "$RDP_IP"
  exe sudo iptables -t nat -D OUTPUT -p tcp -d "${RDP_IP}" --dport "${RDP_PORT}" -j DNAT --to-destination "127.0.0.1:${SSH_PORT}"
 ;;

*)
  echo "Did not understand your argument, please use start|stop"
  ;;

esac
