#!/bin/bash
if [ $# -ne 1 ]; then
  echo "Uso: `basename $0` <url>" 1>&2
  exit 0
fi
echo "$1" | mail -s "$1" add@getpocket.com
exit $?
