#!/bin/bash

SAVEIFS=$IFS
IFS=$(echo -en "\n\b")

for i in $(find ~/.mozilla/firefox/ -maxdepth 1 -type d -name "*.*"); do
  perfil="${i/*./}"
  if [ "$perfil" != "default" ]; then
    desktop="$HOME/.local/share/applications/firefox-$perfil.desktop"
    if [ ! -f  $desktop ]; then
      echo "Creating $desktop"
cat > "$desktop" <<EOL
[Desktop Entry]
Version=1.0
Name=Firefox $perfil
Comment=Run Firefox with $perfil profile
Comment[es]=Arrancar Firefox con el perfil $perfil
Exec=firefox -P $perfil -no-remote
Icon=firefox
Terminal=false
StartupNotify=false
X-MultipleArgs=false
Type=Application
Categories=GNOME;GTK;Network;WebBrowser;
MimeType=text/html;text/xml;application/xhtml+xml;application/xml;application/rss+xml;application/rdf+xml;image/gif;image/jpeg;image/png;x-scheme-handler/http;x-scheme-handler/https;x-scheme-handler/ftp;x-scheme-handler/chrome;video/webm;application/x-xpinstall;
StartupNotify=true
EOL
    fi
  fi
done


for i in $(find ~/.config/chromium/ -maxdepth 1 -type d -name "Profile *"); do
  perfil_dir="${i/*\//}"
  perfil_name="${perfil_dir/* /}"
  perfil="${perfil_name/ /_}"
  desktop="$HOME/.local/share/applications/chromium-$perfil.desktop"
  if [ ! -f  $desktop ]; then
    echo "Creating $desktop"
cat > "$desktop" <<EOL
[Desktop Entry]
Version=1.0
Name=Chromium $perfil_name
Comment=Run Chromium with $perfil_name profile
Comment[es]=Arrancar Chromium con el perfil $perfil_name
Exec=chromium --profile-directory="$perfil_dir" %U
Terminal=false
X-MultipleArgs=false
Type=Application
Icon=chromium-browser
Categories=Network;WebBrowser;
MimeType=text/html;text/xml;application/xhtml_xml;x-scheme-handler/http;x-scheme-handler/https;
StartupWMClass=Chromium-browser
StartupNotify=true
EOL
  fi
done

IFS=$SAVEIFS
