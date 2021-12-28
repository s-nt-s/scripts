#!/bin/bash
set -e

function ask {
  local myvar=""
  local question=""
  if [ -z "$3" ]; then
    question="# $2: "
  else
    question="# $2: [$3]"
  fi
  read "$1" "$question" myvar
  if [ -z "$myvar" ]; then
     myvar="$3"
  fi
  echo "$myvar"
}

PROXYADD=$(ask -p  "Proxy" "${http_proxy##*/}")
USERNAME=$(ask -p  "Username" "$(whoami)")
USERPASS=$(ask -sp "Password")
echo ""
if [ -z "$USERPASS" ]; then
   echo "Password mandatory"
   exit 1
fi

URL="http://detectportal.firefox.com/success.txt"
echo "$ curl --proxy-user $USERNAME:******** --proxy $PROXYADD $URL"

curl --proxy-ntlm --proxy-user "$USERNAME:$USERPASS" --proxy "$PROXYADD" "$URL"
