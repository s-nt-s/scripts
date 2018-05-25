#!/bin/bash

if [ ! -d "$1" ]; then
    echo "Debe dar un directorio como parametro"
    exit 1
fi

TARGET=$(realpath "$1")

FILE=""
cd $(mktemp -d)

function dwn() {
	log=$(mktemp -p .)
	LANG=en_EN wget -o $log --content-disposition "$3"
	if [[ $? -eq 0 ]]; then
		FILE=$(tail -n 3 $log | grep "." | tail -n 1 | sed 's/.*['\''"“]\(.*\)['\''"”].*/\1/')
		if [ ! -f "$FILE" ]; then
            return 1
		fi
        rm "$log"
        NAME="$FILE"
        if [ "$1" == "chromium" ]; then
            VER=$(exiftool $FILE | grep "Product Version\s*:" | sed 's/.*: //')
            NAME="$1_x$2_v$VER.exe"
        fi
        if [ "$1" == "firefox" ]; then
            VER=$(echo "$FILE" | sed 's/.* \([0-9\.]*\)\.exe/\1/')
            NAME="$1_x$2_v$VER.exe"
        fi
        echo "$NAME"
        mv "$FILE" "$TARGET/$NAME"
	fi
}


dwn firefox 64 "https://download.mozilla.org/?product=firefox-latest-ssl&os=win64&lang=es-ES"
dwn firefox 32 "https://download.mozilla.org/?product=firefox-latest-ssl&os=win&lang=es-ES"

REV_64=$(curl -s https://storage.googleapis.com/chromium-browser-snapshots/Win_x64/LAST_CHANGE)
REV_32=$(curl -s https://storage.googleapis.com/chromium-browser-snapshots/Win/LAST_CHANGE)

dwn chromium 64 "https://storage.googleapis.com/chromium-browser-snapshots/Win_x64/$REV_64/mini_installer.exe"
dwn chromium 32 "https://storage.googleapis.com/chromium-browser-snapshots/Win/$REV_32/mini_installer.exe"

PIDGIN=$(curl -s "https://sourceforge.net/projects/pidgin/rss?path=/Pidgin" | grep -- "-offline.exe/download</guid>" | sed 's/.*<guid>\(.*\)<\/guid>/\1/' | head -n 1
)

dwn pidgin 32 $PIDGIN

wget --quiet --accept-regex ".*download.*\.exe$" -r --execute robots=off --content-disposition --no-directories --adjust-extension --convert-links "https://www.claws-mail.org/win32/"


NOTEPAD=$(curl --silent https://notepad-plus-plus.org/download/ -I | grep "^Location: " | cut -d' ' -f2 | tr -d '\r')
wget --quiet -A exe -r --accept-regex ".*\.exe$" --execute robots=off --content-disposition --no-directories --adjust-extension --convert-links "$NOTEPAD"

mv *.exe "$TARGET"

wget --quiet --execute robots=off --content-disposition --no-directories --adjust-extension --convert-links --span-hosts -r --accept-regex ".*download.*\.zip" --domains=download.mobatek.net "https://mobaxterm.mobatek.net/download-home-edition.html"

ls -t MobaXterm_*.zip | tail -n +3 | xargs rm --

mv *.zip "$TARGET"
