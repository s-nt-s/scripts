#!/bin/bash

# https://askubuntu.com/questions/2389/how-to-list-manually-installed-packages
# comm -23 <(aptitude search '~i !~M' -F '%p' | sed "s/ *$//" | sort -u) <(gzip -dc /var/log/installer/initial-status.gz | sed -n 's/^Package: //p' | sort -u)
# https://askubuntu.com/questions/247841/how-can-i-list-the-unused-applications

PC="/tmp/popularity-contest.txt"
NOW=$(date +%s)

if [ ! -f "$PC" ]; then
   popularity-contest > "$PC"
fi

function get_days {
   D=$(echo "$1" | cut -d' ' -f1 | sort -r | head -n 1)
   T=$(echo "$1" | cut -d' ' -f2 | sort -r | head -n 1)
   F=$(echo "$1" | cut -d' ' -f3 | sort -r | head -n 1)
   F="/var/lib/dpkg/info/$F.list"
   if [ $T -gt $D ]; then
      D="$T"
   fi
   if [ $D -eq 0 ] && [ -f "$F" ]; then
      D=$(stat -c '%Y' "$F")
   fi
   D=$(($NOW-$D))
   D=$(($D/(3600*24)))
   D=$(printf '%5s' "$D")
   echo "$D"
}

(
(
comm -23 <(apt-mark showmanual | sort -u) <(gzip -dc /var/log/installer/initial-status.gz | sed -n 's/^Package: //p' | sort -u) | while read p; do
   DT=$(grep " $p " "$PC")
   if [ ! -z "$DT" ]; then
      SZ=$(dpkg-query -Wf '${Installed-Size}\n' "$p" | sort -r | head -n 1)
      if [ -z "$SZ" ]; then
         SZ="¿?¿?"
      else
         SZ=$(($SZ*1024))
         SZ=$(numfmt --to=iec "$SZ")
      fi
      DY=$(get_days "$DT")
      echo "$SZ $DY $p"
   fi
done
du -hs /var/lib/snapd/snaps/* | sed -e 's|[ \t]*/var/lib/snapd/snaps/| |' | while read s p; do
   echo "$s ¿?¿? $p"
done
flatpak list --app -d | head -n -1 | awk '{gsub(/B/, "", $6);U=toupper($6);print $5U,"¿?¿?",$1}'
) | sort -h
) | column -t -s' ' | sed -E 's|([^ ]*)( *) ([^ ]*)( *) ([^ ]*)|\2\1 \4\3 \5|'
