#!/bin/bash

if [ -f "$1" ]; then
  rm "$1"
fi

DIR=$(dirname "$1")
mkdir -p "$DIR"

if [ $? -ne 0 ]; then
  echo "$1 is a wrong path"
  exit $?
fi
if touch "$1" ; then
  rm "$1"
else
  echo "$1 is a wrong path"
  exit $?
fi

7z a -t7z "$1" -m0=lzma2 -mx=9 -aoa -mfb=64 -md=32m -ms=on -mhe *
