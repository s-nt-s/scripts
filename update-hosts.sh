#!/bin/bash

TARGET="/etc/hosts"

if [ "$1" = "--install" ]; then
    FILE=$(basename $0)
    REAL=$(realpath $0)
    CMD=${FILE%.*}
    LINK1="/etc/network/if-up.d/$CMD"
    LINK2="/etc/network/if-post-down.d/$CMD"
    ln -f -s "$REAL" "$LINK1"
    ln -f -s "$REAL" "$LINK2"
    echo "Now you can do custom zones in $TARGET like that:"
    echo '
#### HOME
##
## SSID WIFIA64E
##  MAC c4:05:20:32:b8:4b
##
#
# 192.168.1.30    external.domain.com
#
####

so
# 192.168.1.30    external.domain.com
will be uncommented when you are connected to WIFIA64E by WIFI or a router with mac c4:05:20:32:b8:4b'
    exit 0
fi

#SSID=$(LANG=en_EN nmcli -t -f active,ssid dev wifi | egrep '^yes' | cut -d: -f2)
SSID=$(iwgetid -r)
MAC=$(ip route show match 0/0 | grep default | awk '{print $3}' | sort | uniq | xargs -I{} bash -c "ip neigh | grep {} | awk '{print \$5}' | sort | uniq")

awk -i inplace -v SSID="$SSID" -v MAC="$MAC" '
    BEGIN {
        config_zone=0;
        comment=1;
    }
    $1 == "####" {
        comment=1
        if (config_zone==0) config_zone = 1;
        else config_zone = 0;
        print $0;
        next;
    }
    config_zone == 1 && $1 == "##" && ($2 == "SSID" || $2 == "MAC") {
        if ($2 == "SSID" && SSID != "" && SSID == $3) comment = 0;
        if ($2 == "MAC"  &&  MAC != "" &&  MAC == $3) comment = 0;
        print $0;
        next;
    }
    config_zone == 1 && $1 == "#" && comment == 0 {
        line = $0
        sub(/^#\s*/,"", line);
        print line;
        next;
    }
    config_zone == 1 && $1 !~ /^#+/ && comment == 1 {
        print "#", $0;
        next;
    }
    {
        print $0;
    }
' $TARGET

