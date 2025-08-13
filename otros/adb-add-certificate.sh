#!/bin/bash
openssl x509 -inform PEM -subject_hash_old -in "$1" | head -1
cert_name=$(mktemp)
cat "$1" > $cert_name
openssl x509 -inform PEM -text -in "$1" -out nul >> $cert_name
adb shell mount -o rw,remount,rw /system
adb push $cert_name /system/etc/security/cacerts/
adb shell mount -o ro,remount,ro /system
#adb reboot
