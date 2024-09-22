#!/bin/bash

if [ ! -f "$1" ]; then
    echo "El primer argumento debe ser un fichero"
    exit 1
fi

PY="$(dirname "$1")/.venv/bin/python"

if [ ! -f "$PY" ]; then
    echo "No existe $PY"
    exit
fi

$PY "$@"