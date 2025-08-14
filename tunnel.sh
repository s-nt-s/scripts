#!/bin/bash

DIR=~/.ssh/tunnels
CNF="$DIR/config"

LB_CNF=$(echo "$CNF" | sed "s|${HOME}/|~/|g")

if [ ! -f $CNF ]; then
  echo "$LB_CNF no encontrado"
  exit 1
fi

TNLS=($(grep -ohE "^(\S+): " ~/.ssh/tunnels/config | cut -d':' -f1 | sort))
TNLS=$(printf " %s" "${TNLS[@]}")
TNLS=${TNLS:1}

MODE=""

if [ "$1" == "start" ] || [ "$1" == "stop" ]; then
    MODE="$1"
    shift
fi

if [ -z "$1" ]; then
  echo "Debe pasar como argumento un nombre de tunel registrado en $LB_CNF"
  if [ ! -z "$TNLS" ]; then
    echo "Tuneles disponibles: $TNLS"
  fi
  exit 1
fi

TN="$1"
LN=$(grep "^${TN}: " "$CNF")

if [ -z "$LN" ]; then
  echo "$TN no encontrado en $LB_CNF"
  if [ ! -z "$TNLS" ]; then
    echo "Tuneles disponibles: $TNLS"
  fi
  exit 1
fi

exe() {
  CM=$(echo "$@" | sed "s|${HOME}/|~/|g")
  echo "\$ $CM"
  "$@"
}
exe_nohup() {
  CM=$(echo "$@" | sed "s|${HOME}/|~/|g")
  echo "\$ $CM"
  nohup "$@" >/dev/null 2>&1 &
}

LN=$(echo "${LN#*: }" | sed 's/\s\s*/ /g' | sed 's/^\s*|\s*$//g')
TG=$(echo "$LN" | rev | cut -d' ' -f1 | rev)

CNT="$DIR/$TN.control"
if [ "$MODE" == "start" ] && [ -e "$CNT" ]; then
    exit 0
fi
if [ "$MODE" == "stop" ] && [ ! -e "$CNT" ]; then
    exit 0
fi

if [ -e "$CNT" ]; then
  echo "# $TN va a ser finalizado"
  exe ssh -S "$CNT" -O exit $TG
else
  echo "# $TN va a ser iniciado"
  if command -v autossh >/dev/null 2>&1; then
      exe_nohup autossh -M 0 -o ControlMaster=yes -o ControlPersist=yes -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -S "$CNT" $LN
  else
      exe ssh -f -M -o ControlPersist=yes -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -S "$CNT" $LN
  fi
fi
