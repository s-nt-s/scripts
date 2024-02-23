#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "Necesita ser root para ejecutar este script"
  exit 1
fi

df -h /
echo ""

if command -v deborphan &> /dev/null; then
echo "Limpiando paquetes huerfanos ..."
deborphan | xargs apt-get -y remove --purge
else
echo "WARNING: considere instalar deborphan pàra poder limpiar paquetes huerfanos"
fi

echo "Limpiando archivos de configuración obsoletos ..."
PK="$(COLUMNS=200 dpkg -l | grep "^rc" | tr -s ' ' | cut -d ' ' -f 2)"
if [ ! -z "$PK" ]; then
  dpkg --purge $PK
fi

echo "Limpiando paquetes almacenados en la cache ..."
aptitude -y autoclean
aptitude -y clean
apt clean -y
apt autoclean -y
apt autoremove -y

echo "Borrando thumbnails ..."
if [ -d ~/.thumbnails ]; then
  find ~/.thumbnails -type f -atime +7 -exec rm {} \;
fi
if [ -d ~/.cache/thumbnails ]; then
  rm -rf ~/.cache/thumbnails/*
fi

echo "Eliminando logs antiguos ..."
journalctl --vacuum-time=3d

if command -v snap &> /dev/null; then
echo "Eliminando span disabled ..."
LANG=en_EN snap list --all | awk '/disabled/{print $1, $3}' |  while read snapname revision; do
  snap remove "$snapname" --revision="$revision"
done
fi

if command -v flatpak &> /dev/null; then
echo "Eliminando flatpak unused ..."
flatpak uninstall --unused --assumeyes
rm -rf /var/tmp/flatpak-cache-*
fi

if command -v docker &> /dev/null; then
echo "Eliminando restos de docker..."
docker system prune --force
fi

echo ""
df -h /
