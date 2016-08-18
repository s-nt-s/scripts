#!/bin/sh
IP=$(curl -s icanhazip.com)
if [ -z "$IP" ]; then
	IP=$(curl -s ifconfig.me)
fi
if [ -z "$IP" ]; then
        exit 1
fi
echo "$IP"
exit 0

