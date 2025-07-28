#!/bin/bash
SRC="$1"
OUT="$2"

if [ ! -f "$SRC" ]; then
   echo "$SRC no es un fichero"
   exit 1
fi
if [ ! -d "$OUT" ]; then
   echo "$OUT no es un directorio"
   exit 1
fi

NAME=$(basename -- "$SRC")
LAST=$(find "$OUT" -maxdepth 1 -name "*$NAME" | tail -n 1)
if [ -f "$LAST" ]; then
if cmp -s "$SRC" "$LAST"; then
   echo "$LAST"
   exit 1
fi
fi
FCH="$(date +%Y.%m.%d_%H.%M.%S)"
LAST="${OUT}/${FCH}_${NAME}"
cp "$SRC" "$LAST"
echo "$LAST"
