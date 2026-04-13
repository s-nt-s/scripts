#!/bin/bash
set -euo pipefail

SCRIPT="$(realpath "$1")"
shift

DIR="$(dirname "$SCRIPT")"

if [ -x "$DIR/.venv/bin/python" ]; then
    PYTHON="$DIR/.venv/bin/python"
elif [ -x "$DIR/venv/bin/python" ]; then
    PYTHON="$DIR/venv/bin/python"
else
    echo "python venv not found" >&2
    exit 1
fi

"$PYTHON" "$SCRIPT" "$@"
