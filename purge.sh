#!/bin/bash

echo "Limpiando paquetes huerfanos"
deborphan | xargs apt-get -y remove --purge

echo "Limpiando archivos de configuración obsoletos ... "
dpkg --purge $(COLUMNS=200 dpkg -l | grep "^rc" | tr -s ' ' | cut -d ' ' -f 2)
#echo "OK"

echo "Limpiando paquetes almacenados en la cache ... "
aptitude autoclean
aptitude clean
#echo "OK"

echo "Borrando thumbnails ... "
find ~/.thumbnails -type f -atime +7 -exec rm {} \;
#echo "OK"
