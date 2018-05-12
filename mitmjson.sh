#!/bin/bash

DIR=$(dirname $(realpath $0))

mitmdump --flow-detail 0 -s "$DIR/mitmjson.py" | sed '/:.* \(clientdisconnect\|clientconnect\)/d'
