#!/bin/bash
if [ "$PAM_TYPE" != "open_session" ]; then
	exit 0
fi
if [ "${PAM_RHOST:0:10}" = "192.168.1." ]; then
	exit 0
fi

USER="$PAM_USER@$PAM_RHOST"
if [ -z "$PAM_RHOST" ]; then
	USER="$PAM_USER"
fi

sudo say $(date "+%d/%m/%Y %H:%M")" > $USER inicia $PAM_SERVICE en TTY $PAM_TTY" &

#{
#   echo "User: $PAM_USER"
#   echo "Remote Host: $PAM_RHOST"
#   echo "Service: $PAM_SERVICE"
#   echo "TTY: $PAM_TTY"
#   echo "Date: `date`"
#   echo "Server: `uname -a`"
#} | sudo say &
exit 0
