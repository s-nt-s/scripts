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
/.local/bin
/.local/lib
/.local/share/Trash
EOL

printf "%s\0" "${HOMES[@]}" | xargs -0 -I{} find '{}' -maxdepth 1 -name '.*' | sed 's|.*/|/|' | grep -v -E '/\.(config|icons|local|mozilla|pingus|purple|pynagram|texmf-var|TeXworks|thunderbird|aws|aws-sam|cdk|cert|claws-mail|davmail.properties|ecryptfs|eteks|face|filezilla|gconf|gdfuse|gnupg|hedgewars|kube|netrc|k8slens|pgpass|Private|proxychains|psql_history|python_history|RapidSVN|pypirc|sqlite_history|ssh|subversion|vscode|xmpp.yml|docker|profile.*|pgadmin.*|git.*|elect.*|dbeaver.*|bash.*|bit.*|mysql.*|shar.*-ri.*b)$' | sort | uniq >> "${OUT}exclude.txt"

echo "/etc -> {OUT}etc.tar.gz"
find /etc/cron* /etc/fstab /etc/host* /etc/systemd/ /etc/nginx /etc/apache2/ /etc/aliases /etc/environment /etc/sudo* ! -empty -exec tar czf "${OUT}etc.tar.gz" {} +
for DHM in "${HOMES[@]}"; do
   HOUT="${OUT}$(basename $DHM)"
   echo "$DHM -> $HOUT"
   sudo rsync --info=progress2 -azh --delete --delete-excluded --exclude-from="${OUT}exclude.txt" "$DHM" "$HOUT"
done

