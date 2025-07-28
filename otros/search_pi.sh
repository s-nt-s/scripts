#!/bin/bash

for m in $(ip -o -f inet addr show | grep "scope global" | sed 's/  */ /g' | cut -d' ' -f4 | sed 's/\.[0-9]*\/24/.0\/24/' | sort | uniq | grep -v ^172.); do
   nmap -oG - -sn "$m" | grep -E "^Host:" | sed 's/\s\s*/ /g' | cut -d' ' -f2-3 | sed -E 's/(.*) \((.*)\)/\1\t\2/'
   for ip in $(nmap -oG - -p 80 -n $m | grep -E "Ports: 80/(filtered|open)" | sed 's/  */ /g' | cut -d' ' -f2 | sort | uniq); do
      if [ "$(curl -qs http://$ip/ping)" == "pong" ]; then
         echo $ip
         exit
      fi
   done
done
