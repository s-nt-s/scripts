#!/bin/bash
if [ "$1" == "--install" ]; then
  NAME=$(basename $0)
  NAME=${NAME%.*}
  SCRIPT=$(realpath $0)
  DESKTOP="$HOME/.config/autostart/$NAME.desktop"
  echo "Creating $DESKTOP"
cat > "$DESKTOP" <<EOL
[Desktop Entry]
Encoding=UTF-8
Version=0.9.4
Type=Application
Name=Brightness
Name[es]=Brillo
Comment=Default brightness
Comment[es]=Brillo por defecto
Exec=sudo $SCRIPT
OnlyShowIn=XFCE;
StartupNotify=false
Terminal=false
Hidden=false
EOL
elif [ -f /sys/class/backlight/acpi_video0/brightness ]; then
	echo "0" > /sys/class/backlight/acpi_video0/brightness
fi
