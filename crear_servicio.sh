#!/bin/bash

if [[ $(/usr/bin/id -u) -ne 0 ]]; then
    echo "Necesita ejecutar como root"
    exit
fi

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
		ENLACE="/etc/systemd/system/$CMD.service"
		if [ -e "$ENLACE" ]; then
			echo "Ya existe un servicio con ese nombre:"
			echo -n -e "\t"
			ls -l "$ENLACE"
		else
cat > "$ENLACE" <<EOL
[Unit]
Description=$CMD Service

[Service]
Type=idle
ExecStart=$RUTA

[Install]
WantedBy=multi-user.target
EOL
			let COUNT=COUNT+1
			OKS="$OKS $ENLACE"
		fi
    else
    	echo "$s no es un script ejecutable"
    fi
done

if [ "$COUNT" -ne 0 ]; then
	echo "Servicios creados:"
	ls -l $OKS | sed 's/[^\/]*/\t/'
    echo "Falta habilitarlos e iniciarlos:"
    echo "	sudo systemctl daemon-reload"
    echo "	sudo systemctl enable $CMD.service"
fi
