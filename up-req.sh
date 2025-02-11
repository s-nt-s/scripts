#!/bin/bash

RQ="$1"
if [ -z "$RQ" ]; then
    RQ="./requirements.txt"
fi

if [ ! -f "$RQ" ]; then
    echo "File not found: $RQ"
    exit 1
fi

NOTFOUND=()

while read -r lib; do
    l=$(echo "$lib" | sed -e 's/\[.*//g' )
    VS=$(pip show "$l" 2>/dev/null | grep -E "^Version: " | awk '{print $2}')
    if [ -n "$VS" ]; then
        echo "$lib==$VS"
    else
        NOTFOUND+=("$lib")
    fi
done < <(sed -e 's/[=~<> ].*//g' -e 's/^\s*|\s*$//g' -e '/^\s*$/d' -e '/^#/d' "$RQ" | sort | uniq)

if [ ${#NOTFOUND[@]} -gt 0 ]; then
    echo "# The following packages were not found:"
    for lib in "${NOTFOUND[@]}"; do
        escaped_lib=$(printf '%s\n' "$lib" | sed 's/[][\.*^$(){}?+|/]/\\&/g')
        grep -E "^$escaped_lib([=~<>].*)?$" "$RQ"
    done
fi
