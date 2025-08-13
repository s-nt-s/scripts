#!/bin/bash

FM="$1"
SZ="$2"

if [ -z "$FM" ]; then
   echo "Ha de pasar como argumento el formato de salida"
   exit 1
fi

if [ -z "$SZ" ]; then
   SZ="800x800>"
fi

mogrify -strip +repage -fuzz 600 -resize "$SZ" -format "$FM" -- *.xcf
