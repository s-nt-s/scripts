#!/bin/bash
set -e

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
  echo "Debe pasar como argumento un nombre de túnel registrado en $LB_CNF"
  if [ ! -z "$TNLS" ]; then
    echo "Túneles disponibles: $TNLS"
  fi
  exit 1
fi

TN="$1"
LN=$(grep "^${TN}: " "$CNF")

if [ -z "$LN" ]; then
  echo "$TN no encontrado en $LB_CNF"
  if [ ! -z "$TNLS" ]; then
    echo "Túneles disponibles: $TNLS"
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
MSH="$DIR/$TN.monitor.sh"
LOG="$DIR/$TN.log"
if [ "$MODE" == "start" ] && [ -e "$CNT" ]; then
    echo "# $TN ya está iniciado"
    exit 0
fi
if [ "$MODE" == "stop" ] && [ ! -e "$CNT" ]; then
    echo "# $TN ya está finalizado"
    exit 0
fi

if [ -e "$CNT" ]; then
  echo "# $TN va a ser finalizado"
  exe ssh -S "$CNT" -O exit $TG
  if [ -f "$MSH" ]; then
    pkill -f "$MSH"
    rm -f "$MSH" "$LOG"
  fi
else
  echo "# $TN va a ser iniciado"
  cat > "$MSH" <<EOF
#!/bin/bash
set -e
sec=\$(date +%S)
wait=\$((60 - sec))
sleep \$wait
while true; do
  sleep 30
  if ssh -S "$CNT" -O check "$TG" >/dev/null 2>&1; then
    echo "\$(date '+%Y-%m-%d %H:%M:%S') $TN activo"
  else
    echo "\$(date '+%Y-%m-%d %H:%M:%S') $TN caído"
    ssh -f -M -o ControlPersist=yes -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -S $CNT $LN
  fi
done
EOF
  CMD=$(grep -Eoh "^\s+ssh\s+.*" "$MSH" | sed 's/^\s*//')
  exe $CMD
  chmod +x "$MSH"
  nohup "$MSH" >> "$LOG" 2>&1 &
fi
