#!/bin/bash
set -e
git rev-parse --is-inside-work-tree 2>&1 > /dev/null
if [ $? -ne 0 ]; then
  exit $?
fi
BR=$(git branch | grep "^\*" | sed 's|.* ||')
if [ "$BR" != "master" ] && [ "$BR" != "main" ]; then
  echo "Has de estar en la rama master or main"
  exit 1
fi
git pull
git checkout --orphan nuevo_comienzo
git add -A
git commit -am "first commit"
git branch -D "$BR"
git branch -m "$BR"
git push -f origin "$BR"
git gc --aggressive --prune=all
