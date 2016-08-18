#!/bin/bash
if [ -f /sys/class/backlight/acpi_video0/brightness ]; then
	echo "0" > /sys/class/backlight/acpi_video0/brightness
fi
