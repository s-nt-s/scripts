#!/bin/bash
find . -type f -name "*.py" -print0 | xargs -0 sed -i '1 s/^#!\/usr\/bin\/python/#!\/usr\/bin\/env python/'
find . -type f -executable -name "*.py" | while read f; do
  fl=$(head -n 1 "$f" | cut -c1-2)
  if [ "$fl" != "#!" ]; then
    sed '1i#!/usr/bin/env python3\n' -i "$f"
  fi
done
autoflake --in-place --recursive .
autopep8 --in-place --recursive .
isort -rc .

if [ -f ./requirements.txt ] || [ "$1" == "-r" ]; then
  pipreqs . --force
  if grep -q "beautifulsoup4" requirements.txt; then
  if grep -q -e "[\"']lxml[\"']" --include="*.py" -r .; then
    pip3 freeze | grep lxml >> requirements.txt
  fi
  fi
  sort -o requirements.txt requirements.txt
fi
