#!/bin/sh
set -e
git rev-parse --is-inside-work-tree 2>&1 > /dev/null
if [ $? -ne 0 ]; then
  exit $?
fi
US=$(git config user.name)
ML=$(git config user.email)
BR=$(git branch | grep "^\*" | sed 's|.* ||')
OLD="$1"
if [ -z "$OLD" ]; then
  echo "Has de pasar como parámetro una dirección de correo:"
  git shortlog --all --summary --email --numbered | sed 's/^.*<\|>.*$//g' | sed "/^${ML}$/d" | sort | uniq
  exit 1
fi

FL='
OLD_EMAIL="'"${OLD}"'"
CORRECT_NAME="'"${US}"'"
CORRECT_EMAIL="'"${ML}"'"
if [ "$GIT_COMMITTER_EMAIL" = "$OLD_EMAIL" ]; then
    export GIT_COMMITTER_NAME="$CORRECT_NAME"
    export GIT_COMMITTER_EMAIL="$CORRECT_EMAIL"
fi
if [ "$GIT_AUTHOR_EMAIL" = "$OLD_EMAIL" ]; then
    export GIT_AUTHOR_NAME="$CORRECT_NAME"
    export GIT_AUTHOR_EMAIL="$CORRECT_EMAIL"
fi
'
git filter-branch --env-filter "$FL" --tag-name-filter cat -- --branches --tags

echo "Comprueba los cambios y si estan bien haz:"
echo "git push --force --tags origin HEAD:${BR}"
