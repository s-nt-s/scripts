#!/bin/bash

flock -nx /tmp/flock.davmail -c davmail &
claws-mail
DAV=$(lsof /tmp/flock.davmail | grep "^java" | sed 's/\s\s*/ /g' | cut -d' ' -f2)

CLW=$(pgrep claws-mail)

if [ -z "$CLW" ]; then
    if [ -n "$DAV" ]; then
        kill "$DAV"
    fi
fi
