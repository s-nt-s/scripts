#!/bin/bash
set -euo pipefail
if [ ! -d "/tmp/oasis/" ]; then
    export OASIS_AI=3
    curl -fsSL https://code.03c8.net/KrakensLab/oasis/archive/master.tar.gz | tar -xz -C /tmp
    cd /tmp/oasis/
    ./install.sh
fi
exec ./oasis.sh $@