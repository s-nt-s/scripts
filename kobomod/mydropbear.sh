#!/bin/sh
#/mnt/onboard/.adds/koreader/scripts/mydropbear.sh

TMP_PID="/tmp/dropbear_koreader.pid"
PORT="$1"

if [ -f "$TMP_PID" ]; then
   cat "$TMP_PID" | xargs kill
   rm -f "$TMP_ID"
   echo "SSH parado"
   exit 0
fi
IP=$(/sbin/ifconfig | /usr/bin/awk '/inet addr/{print substr($2,6)}')

if [ -z "$IP" ]; then
   IP="127.0.0.1"
fi

/bin/mount -t devpts | /bin/grep -q /dev/pts || { /bin/mkdir -p /dev/pts && /bin/mount -t devpts devpts /dev/pts; }
if [ ! -d /dev/pts ]; then
   echo "Error al crear /dev/pts"
   exit 1
fi

export PATH=$PATH:/mnt/onboard/.adds/koreader/scripts
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/mnt/onboard/.adds/koreader/libs
export HOME=/mnt/onboard/.adds/koreader/
cd $HOME
./dropbear -E -R -p "$PORT" -P "$TMP_PID"

if [ $? -ne 0 ]; then
   echo "Error al inciar SSH en $IP:$PORT"
   exit 1
fi

echo "SSH $IP:$PORT iniciado"
exit 0
