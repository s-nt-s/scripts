#!/bin/bash
git rev-parse --is-inside-work-tree 2>&1 > /dev/null
if [ $? -ne 0 ]; then
  exit $?
fi
DIR=$(pwd | sed "s|^${HOME}/|~/|")
echo $DIR
RP=($(git remote -v | awk '$1=="origin" {print $2}' | sort | uniq | sed '/^\s*$/d'))
if [ ${#RP[@]} -eq 1 ]; then
  echo "origin  ${RP[0]}"
else
  git remote -v | grep "^origin"
fi
US=$(git config user.name)
ML=$(git config user.email)
echo "user    $US"
echo "email   $ML"
git branch -r
#git shortlog --all --summary --numbered --email
git shortlog --summary --email --numbered
#git gc --aggressive --prune=all
