#!/bin/bash
if [ ! -d "$1" ]; then
	echo "Ha de pasar un directorio como parametro"
	exit 1
fi

find "$1" -type d -print0 | xargs -0 chmod 0775
find "$1" -type f -print0 | xargs -0 chmod 0664
