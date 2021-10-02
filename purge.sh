#!/bin/bash

if [ "$EUID" -ne 0 ]; then
  echo "Necesita ser root para ejecutar este script"
  exit 1
fi

echo "Limpiando paquetes huerfanos"
deborphan | xargs apt-get -y remove --purge

echo "Limpiando archivos de configuración obsoletos ..."
PK="$(COLUMNS=200 dpkg -l | grep "^rc" | tr -s ' ' | cut -d ' ' -f 2)"
if [ ! -z "$PK" ]; then
  dpkg --purge $PK
fi

echo "Limpiando paquetes almacenados en la cache ..."
aptitude autoclean
aptitude clean
apt clean
apt autoclean
apt autoremove

echo "Borrando thumbnails ..."
if [ -d ~/.thumbnails ]; then
  find ~/.thumbnails -type f -atime +7 -exec rm {} \;
fi
if [ -d ~/.cache/thumbnails ]; then
  rm -rf ~/.cache/thumbnails/*
fi

echo "Eliminando logs antiguos ..."
journalctl --vacuum-time=3d
