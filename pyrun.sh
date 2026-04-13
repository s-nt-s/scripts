#!/bin/bash
set -euo pipefail

SCRIPT="$(realpath "$1")"
shift

DIR="$(dirname "$SCRIPT")"
PARENT="$(dirname "$DIR")"
if [ -x "$DIR/.venv/bin/python" ]; then
    PYTHON="$DIR/.venv/bin/python"
elif [ -x "$PARENT/.venv/bin/python" ]; then
    PYTHON="$PARENT/.venv/bin/python"
else
    echo "python venv not found" >&2
    exit 1
fi

"$PYTHON" "$SCRIPT" "$@"
