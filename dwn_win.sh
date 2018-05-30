#!/bin/bash

if [ ! -d "$1" ]; then
    echo "Debe dar un directorio como parametro"
    exit 1
fi

TARGET=$(realpath "$1")

rm -R "$TARGET"*

cd $(mktemp -d)

function dwn() {
	log=$(mktemp -p .)
	LANG=en_EN wget -o $log --content-disposition "$3"
	if [[ $? -eq 0 ]]; then
		FILE=$(tail -n 3 $log | grep "." | tail -n 1 | sed 's/.*['\''"“]\(.*\)['\''"”].*/\1/')
		if [ ! -f "$FILE" ]; then
            return 1
		fi
        URL=$(grep " https\?://" "$log" | tail -n 1 | rev | cut -d' ' -f1 | rev)
        rm "$log"
        NAME="$FILE"
        ARQ=$2
        if [ $ARQ -eq 0 ]; then
            if [[ $url = *"x64"* ]] || [[ $url = *"64bit"* ]] || [[ $url = *"amd64"* ]]; then
                ARQ=64
            else
                ARQ=32
            fi
        fi
        if [ "$1" == "chromium" ]; then
            VER=$(exiftool $FILE | grep "Product Version\s*:" | sed 's/.*: //')
            NAME="$1_x${ARQ}_v$VER.exe"
        fi
        if [ "$1" == "firefox" ]; then
            VER=$(echo "$FILE" | sed 's/.* \([0-9\.]*\)\.exe/\1/')
            NAME="$1_x${ARQ}_v$VER.exe"
        fi

        DST="${TARGET}/"$ARQ
        mkdir -p "${DST}"
        mv "$FILE" "$DST/$NAME"

        echo "$NAME"
        echo "$NAME" >> "$DST/dwn.log"
        echo "$URL" >> "$DST/dwn.log"
        echo "" >> "$DST/dwn.log"

        DOM=$(echo $URL | awk -F/ '{print $3}')
        
        echo "[$NAME]($NAME) <small>from [$DOM]($URL)</small>" >> "$DST/index.md"
        echo "" >> "$DST/index.md"
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


for url in $(lynx -listonly -nonumbers -dump https://www.claws-mail.org/win32/ | grep "\.exe$"); do
    dwn "claws-mail" 0 "$url"
done

for url in $(lynx -listonly -nonumbers -dump https://notepad-plus-plus.org/download/ | grep "\.exe$"); do
    dwn "notepad-plus-plus" 0 "$url"
done

for url in $(lynx -listonly -nonumbers -dump "https://mobaxterm.mobatek.net/download-home-edition.html" | grep "\.zip$" | head -n 2); do
    dwn mobaxterm 32 "$url"
done

for url in $(lynx -listonly -nonumbers -dump https://www.7-zip.org/download.html | grep "\.\(exe\|msi\)$" | head -n 4); do
    dwn "7z" 0 "$url"
done


for url in $(lynx -listonly -nonumbers -dump http://strawberryperl.com/releases.html | grep "\.\(exe\|msi\|zip\)$" | head -n 4); do
    dwn strawberryperl 0 "$url"
done

for url in $(lynx -listonly -nonumbers -dump https://www.python.org/downloads/windows/ | grep "\.\(exe\|msi\|zip\)$" | grep "ython-3" | grep -v "webinstall" | grep -v "embed" | head -n 2); do
    dwn python 0 "$url"
done


find "$TARGET" -name "index.md" | sed 's/\.[^\.]*$//' | xargs -I {} pandoc -s --from markdown --to html5 {}.md -o {}.html
