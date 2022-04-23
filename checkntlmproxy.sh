#!/bin/bash
set -e

PRM1="$1"

function ask {
  local myvar=""
  local question=""
  if [ -z "$3" ]; then
    question="# $2: "
  else
    question="# $2: [$3] "
  fi
  if [ "$PRM1" == "--ask" ] || [ -z "$3" ]; then
    read "$1" "$question" myvar
  fi
  if [ -z "$myvar" ]; then
     myvar="$3"
  fi
  echo "$myvar"
}

PROXYADD=$(ask -p  "Proxy" "${http_proxy##*/}")
USERNAME=$(ask -p  "Username" "$(whoami)")
if [ "$PRM1" == "--ask" ] || [ -z "$PRM1" ]; then
USERPASS=$(ask -sp "Password")
echo ""
else
USERPASS="$PRM1"
fi
if [ -z "$USERPASS" ]; then
   echo "Password mandatory"
   exit 1
fi

URL="http://detectportal.firefox.com/success.txt"
echo "$ curl --proxy-ntlm --proxy-user $USERNAME:* --proxy $PROXYADD ${URL#*//}"

curl --proxy-ntlm --proxy-user "$USERNAME:$USERPASS" --proxy "$PROXYADD" "$URL"
