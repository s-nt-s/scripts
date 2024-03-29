#!/bin/bash
set -e
function error {
   echo $@
   exit 1
}

OUT="$1"
if [ -z "$OUT" ]; then
   OUT="$(pwd)/"
fi
if [ ! -d "$OUT" ]; then
   error "$OUT no es un direcotrio"
fi
if [[ ${OUT} != *"/" ]];then
   OUT="$OUT/"
fi

if [ "$EUID" -ne 0 ]; then
   error "Necesita ser root para ejecutar este script"
fi

readarray -t HOMES <<< "$(getent passwd | grep -e ':/bin/bash$' | cut -d: -f6 | xargs -I{} find '{}' -maxdepth 0 -type d ! -empty -printf '%p/\n' | sort)"

if [ "${#HOMES[@]}" -eq 0 ]; then
   error "No se han encontrado directorios HOMEs"
fi

echo "Se va a realizar el backup de:"
for DHM in "${HOMES[@]}"; do
    echo "  $DHM"
done
echo "  /etc (solo algunos ficheros)"
for DHM in "${HOMES[@]}"; do
   if [[ "$OUT" == $DHM* ]]; then
      error "No puedes hacer un backup de $DHM en $OUT"
   fi
done

cat > "${OUT}exclude.txt" <<EOL
/francinette
/GNUstep
/nltk_data
/R
/Replays
/Scores
/snap
/CheckPoint
/jd2
EOL


set +e
printf "%s\0" "${HOMES[@]}" | xargs -0 -I{} find '{}' -maxdepth 1 -name '.*' -printf '/%P\n' | sort | uniq | grep -v -E '^\/\.(sendxmpprc|toxmpp|config|icons|local|mozilla|pingus|purple|pynagram|texmf-var|TeXworks|thunderbird|aws|aws-sam|cdk|cert|claws-mail|davmail.properties|ecryptfs|eteks|face|filezilla|gconf|gdfuse|gnupg|hedgewars|kube|netrc|k8slens|pgpass|Private|proxychains|RapidSVN|pypirc|ssh|subversion|vscode|xmpp.yml|docker|bash_aliases|profile.*|pgadmin.*|git.*|elect.*|dbeaver.*|bit.*|mysql.*|shar.*-ri.*b)$' >> "${OUT}exclude.txt"

printf "%s\0" "${HOMES[@]}" | xargs -0 -I{} find '{}' -maxdepth 2 -path '{}.local/*' -printf '/%P\n' | sort | uniq | grep -v -E '^\/\.local/(share)$' >> "${OUT}exclude.txt"

printf "%s\0" "${HOMES[@]}" | xargs -0 -I{} find '{}' -maxdepth 3 -path '{}.local/share/*' -printf '/%P\n' | sort | uniq | grep -v -E '^\/\.local/share/(greg|calibre.*|DBeaver.*|fonts|gajim|gvfs-metadata|keyrings|notes|remmina|Tele.*Desktop|tomboy)$' >> "${OUT}exclude.txt"

printf "%s\0" "${HOMES[@]}" | xargs -0 -I{} find '{}' -maxdepth 2 -path '{}.config/*' -printf '/%P\n' | sort | uniq | grep -v -E '^\/\.config/(geany|greg|calibre.*|chromium|filezilla|freerdp|gajim|google-chrome|hexchat|kdenlive.*|keepassx|Lens|Microsoft.*|mon.*-project|Mumble|remmina|skypeforlinux|teams|tomboy|transmission.*|VirtualBox)$' >> "${OUT}exclude.txt"

printf "%s\0" "${HOMES[@]}" | xargs -0 -I{} find '{}' -maxdepth 2 -path '{}.mozilla/*' -printf '/%P\n' | sort | uniq | grep -v -E '^\/\.mozilla/(firefox)$' >> "${OUT}exclude.txt"

printf "%s\0" "${HOMES[@]}" | xargs -0 -I{} find '{}' -maxdepth 4 -path '{}wks/*' -type d \( -name "venv" -o -name ".venv" -o -name ".env" \) -printf '/%P\n' | sort | uniq >> "${OUT}exclude.txt"

printf "%s\0" "${HOMES[@]}" | xargs -0 -I{} find '{}' -path '{}wks/*' -type d -name "__pycache__" ! \( -path "*/venv/*" -o -path "*/.venv/*" -o -path "*/.env/*" -o -path "*/site-packages/*" \) -printf '/%P\n' | sort | uniq >> "${OUT}exclude.txt"
printf "%s\0" "${HOMES[@]}" | xargs -0 -I{} find '{}' -path '{}wks/*' -type f -name "*.pyc" ! \( -path "*/venv/*" -o -path "*/.venv/*" -o -path "*/__pycache__/*"  -o -path "*/.env/*" -o -path "*/site-packages/*" \) -printf '/%P\n' >> "${OUT}exclude.txt"

#printf "%s\0" "${HOMES[@]}" | xargs -0 -I{} find '{}' -maxdepth 4 -path '{}wks/*' -type d -name "node_modules" -printf '/%P\n' | sort | uniq

find /etc/passwd /etc/shadow /etc/cron* /etc/fstab /etc/host* /etc/systemd/ /etc/nginx /etc/apache2/ /etc/aliases /etc/environment /etc/sudo* /etc/pam.d /etc/transmission-daemon /etc/exim4/passwd.client /etc/letsencrypt /etc/usbmount /etc/ssh /etc/default/sslh -type f ! -name .placeholder ! -empty | sed 's|^/etc||' > "${OUT}etc.txt"

set -e
if [ "$(cat /etc/issue | cut -d' ' -f1 | tr '[:upper:]' '[:lower:]')" == "raspbian" ]; then
cat >> "${OUT}exclude.txt" <<EOL
/.claws-mail
/.eteks
/.gconf
/.hedgewars
/.icons
/.pingus
/.purple
/.pynagram
/.profile
/.local/share/gajim
/.local/share/gvfs-metadata
/.config/geany
/.config/chromium
/.config/gajim
/.config/transmission-remote-gtk
/dwn/podcasts
EOL
fi

DHM="/etc/"
HOUT="${OUT}$(basename $DHM)"
echo "$DHM -> $HOUT"
rsync --info=progress2 -azh --delete --delete-excluded --prune-empty-dirs --files-from="${OUT}etc.txt" "$DHM" "$HOUT"
find "$HOUT" -maxdepth 1 -empty -delete
for DHM in "${HOMES[@]}"; do
   HOUT="${OUT}$(basename $DHM)"
   echo "$DHM -> $HOUT"
   sudo rsync --info=progress2 -azh --delete --delete-excluded --exclude-from="${OUT}exclude.txt" "$DHM" "$HOUT"
   # No uso --prune-empty-dirs porque a maxdepth > 1 hay directorios vacios necesarios
   find "$HOUT" -maxdepth 1 -empty -delete
done

