#!/bin/bash
if [ -z "$1" ]; then
    DIR="."
elif [ ! -d "$1" ]; then
    echo "$1 no es un directorio"
    exit 1
else
    DIR="$1"
fi

find "$DIR" -name "requirements.txt" -exec cat {} \+ | sort -r -u | awk -F "==" '{count[$1]++;} count[$1]==1'
