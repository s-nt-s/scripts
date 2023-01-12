#!/bin/sh

# SOURCE: https://kgibran.wordpress.com/2019/03/13/remmina-rdp-ssh-tunnel-with-pre-and-post-scripts/

scriptname="$(basename $0)"

if [ $# -lt 3 ]; then
    echo "Usage: $scriptname start | stop  RDP_NODE_IP  SSH_NODE_IP"
    exit
fi

case "$1" in

start)

  echo "Starting tunnel to $3"
  ssh -M -S ~/.ssh/$scriptname.control -fnNT -L 3389:$2:3389 $3
  ssh -S ~/.ssh/$scriptname.control -O check $3
  ;;

stop)
  echo "Stopping tunnel to $3"
  ssh -S ~/.ssh/$scriptname.control -O exit $3 
 ;;

*)
  echo "Did not understand your argument, please use start|stop"
  ;;

esac
