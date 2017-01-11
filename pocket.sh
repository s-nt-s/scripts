#!/bin/bash
if [ $# -ne 1 ]; then
  echo "Uso: `basename $0` <url>" 1>&2
  exit 0
fi
URL=$(curl -sLI "$1" | grep -i Location | sed 's/^Location:\s*//')
if [ -z "$URL" ]; then
	URL=$1
fi
echo "$URL" | mail -s "$1" add@getpocket.com
echo "$URL enviada a pocket"
exit $?
