#!/bin/bash
#sudo ifdown eth0
ok() {
        STATE=$(ifconfig eth0 | grep "inet addr:" | sed 's/^ *inet addr/Lan/' | sed 's/  / /g')
	IP=$(getip)
	if [ ! -z "$IP" ]; then
		echo -n "Ip:$IP "
	else
		echo -n "IP ERROR - "
	fi
        echo "$STATE"
}

if [ "$1" == "--log" ]; then
	echo -n $(date "+%d/%m/%Y %H:%M > ")""
fi

if ifconfig eth0 | grep -q "inet addr:"; then
	ok
	exit 0
fi

#ERR=$(sudo ip link set eth0 2>&1)
ERR=$(ifup --force eth0 2>&1)
#sudo ifconfig eth0 up
#ifup --force eth0
#ERR=$(sudo ifconfig eth0 up && ifup --force eth0 2>&1)
OUT=$?
if [ $OUT -eq 0 ] ; then
	echo -n "RESET OK - "
        ok
else
        echo "RESET FAIL - $ERR"
fi
