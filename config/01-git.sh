#!/bin/bash

#git config --global user.name ""
#git config --global user.email ""
git config --global push.default simple
git config --global credential.helper cache
if [ -e ~/.ssh/github ]; then
	git config --global url.ssh://git@github.com/.insteadOf https://github.com/
fi

mkdir -p ~/wks

cd ~/wks

GITS=(scripts)

for i in "${GITS[@]}"
do
	if [ ! -e $i ]; then
		git clone https://github.com/santos82/$i.git
	fi
done

