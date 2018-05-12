#!/bin/bash

if [ "$1" = "--install" ]; then
    FILE=$(basename $0)
    REAL=$(realpath $0)
    CMD=${FILE%.*}
    LINK="/etc/network/if-up.d/$CMD"
    ln -f -s "$REAL" "$LINK"
    echo "Now you can create hosts files for your WIFIs like that:"
    for wiki in $(nmcli -t -f active,ssid dev wifi | cut -d: -f2 | head -n 3); do
        echo "  /etc/hosts.wifi.$wiki"
    done
    exit 0
fi


WIFI=$(LANG=en_EN nmcli -t -f active,ssid dev wifi | egrep '^yes' | cut -d: -f2)
TARGET="/etc/hosts"

for hosts_file in /etc/hosts.wifi.*; do
	while read line; do
		if [ ! -z "$line" ]; then
			sed "/\s*$line\s*/d" -i "$TARGET"
		fi
	done < $hosts_file
done

hosts_file="/etc/hosts.wifi.$WIFI"
if [ -f "$hosts_file" ]; then
    cat "$hosts_file" >> $TARGET
fi

