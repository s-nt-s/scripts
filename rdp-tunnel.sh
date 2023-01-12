#!/bin/sh

# SOURCE: https://kgibran.wordpress.com/2019/03/13/remmina-rdp-ssh-tunnel-with-pre-and-post-scripts/

scriptname="$(basename $0)"

if [ $# -lt 4 ]; then
    echo "Usage: $scriptname start | stop RDP_NODE_NAME SSH_NODE_IP SSH_TUNNEL_PORT"
    exit
fi

exe() {
  CM=$(echo "$@" | sed "s|${HOME}/|~/|g")
  echo "\$ $CM"
  "$@"
}

RDP_NODE_NM="$2"
SSH_NODE_IP="$3"
SSH_TUNN_PT="$4"

if [[ "$SSH_TUNN_PT" == *":"* ]]; then
  SSH_TUNN_PT=$(echo "$SSH_TUNN_PT" | sed 's/.*://')
fi


CRL="/tmp/ssh_${scriptname}_${RDP_NODE_NM}_${SSH_NODE_IP}_${SSH_TUNN_PT}.control"

case "$1" in

start)

  echo "Starting tunnel to $RDP_NODE_NM"
  exe ssh -M -S "$CRL" -fnNT -L "${SSH_TUNN_PT}:${RDP_NODE_NM}:3389" "$SSH_NODE_IP"
  exe ssh -S "$CRL" -O check "$RDP_NODE_NM"
  ;;

stop)
  echo "Stopping tunnel to $RDP_NODE_NM"
  exe ssh -S "$CRL" -O exit "$RDP_NODE_NM"
 ;;

*)
  echo "Did not understand your argument, please use start|stop"
  ;;

esac
