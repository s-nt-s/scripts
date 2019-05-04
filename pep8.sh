#!/bin/bash
find . -type f -name "*.py" -print0 | xargs -0 sed -i '1 s/^#!\/usr\/bin\/python/#!\/usr\/bin\/env python/'
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
