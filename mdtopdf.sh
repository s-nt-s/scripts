#!/bin/bash
if [ ! -f "$1" ]; then
   echo "Fichero no existe: $1"
   exit 1
fi
SCR="$(realpath -- $0)"
CSS="${SCR%.*}.css"
pandoc --pdf-engine=weasyprint --css="$CSS" -o "$1.pdf" $@
