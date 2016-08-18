#!/bin/bash

if [ "$#" -eq 0 ]; then
    echo "Debe pasar como parametro al menos un script ejecutable"
fi

COUNT=0
OKS=""
for s in "$@"
do
    if [ -x "$s" ]; then
		FILE=$(basename $s)
		CMD=${FILE%.*}
		RUTA=$(realpath $s)
		ENLACE="/usr/local/bin/$CMD"
		if [ -L "$ENLACE" ]; then
			if [ -e "$ENLACE" ]; then
				DESTINO=$(realpath "$ENLACE")
				if [ "$RUTA" == "$DESTINO" ]; then
					let COUNT=COUNT+1
					OKS="$OKS $ENLACE"
				else
					echo "Ya existe el enlace:"
					ls -l $ENLACE | sed 's/[^\/]*/\t/'
				fi
			else
				DESTINO=$(basename $(ls -l "$ENLACE" | sed 's/.* -> //'))
				if [ "$FILE" == "$DESTINO" ]; then
					sudo ln -f -s "$RUTA" "$ENLACE"
					let COUNT=COUNT+1
					OKS="$OKS $ENLACE"
				else
					echo "Enlace roto:"
					ls -l $ENLACE | sed 's/[^\/]*/\t/'
				fi
			fi
		elif [ -e "$ENLACE" ]; then
			echo "Ya existe un fichero con ese nombre:"
			echo -n -e "\t"
			ls -l "$ENLACE"
		else
			sudo ln -s "$RUTA" "$ENLACE"
			let COUNT=COUNT+1
			OKS="$OKS $ENLACE"
		fi
    else
    	echo "$s no es un script ejecutable"
    fi
done

if [ "$COUNT" -ne 0 ]; then
	echo "Enlaces creados:"
	ls -l $OKS | sed 's/[^\/]*/\t/'
fi
