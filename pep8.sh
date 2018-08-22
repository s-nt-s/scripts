#!/bin/bash
autoflake --in-place --recursive .
autopep8 --in-place --recursive .
isort -rc .

if [ -f ./requirements.txt ]; then
    pipreqs --print . | sort > requirements.txt
fi
