#!/bin/bash

cd

apt-get update

apt-get install -y $(check-language-support --show-installed -l es_ES)
localectl set-locale LANG=es_ES.UTF-8

cp .profile .profile.bak

cat <<EOT >> .profile

localectl set-locale LANG=es_ES.UTF-8
setxkbmap -layout es
EOT
