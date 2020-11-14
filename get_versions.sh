#!/bin/bash

######
## Based on
## https://stackoverflow.com/questions/12850030/git-getting-all-previous-version-of-a-specific-file-folder
#####

# we'll write all git versions of the file to this folder:
EXPORT_TO="$(mktemp -d)"
USAGE="Please cd to the root of your git proj and specify path to file you with to inspect (example: $0 some/path/to/file)"
echo "Export to $EXPORT_TO"

for GIT_PATH_TO_FILE in "$@"; do

# extract just a filename from given relative path (will be used in result file names)
GIT_SHORT_FILENAME=$(basename $GIT_PATH_TO_FILE)

# reset coutner
COUNT=0

# iterate all revisions
git rev-list --all --objects -- ${GIT_PATH_TO_FILE} | \
    cut -d ' ' -f1 | \
while read h; do \
     COUNT=$((COUNT + 1)); \
     COUNT_PRETTY=$(printf "%04d" $COUNT); \
     PRT=$(git show $h | head -3 | grep 'Date:') \
     COMMIT_DATE=`git show $h | head -3 | grep 'Date:' | awk '{print $4"-"$3"-"$6" "$5}'`; \
     if [ "${COMMIT_DATE}" != "" ]; then \
         COMMIT_DATE=$(date -d "$COMMIT_DATE" +'%Y-%m-%d_%H-%M-%S')
         OUT="${EXPORT_TO}/${COMMIT_DATE}.${COUNT_PRETTY}.${h}.${GIT_SHORT_FILENAME}"
         git cat-file -p ${h}:${GIT_PATH_TO_FILE} > ${OUT} 2>/dev/null;\
         if [ $? -ne 0 ]; then
           rm "${OUT}"
         fi
     fi;\
done

done
cd "${EXPORT_TO}"
function check_prefix() {
  PRE="$1"
  CHK=$(ls | cut -b "1-${PRE}" | uniq -c | grep "^\s*[2-9]" | wc -l)
  if [ "$CHK" -eq 0 ]; then
    RST=$((24-PRE))
    rename "s/(.{${PRE}}).{${RST}}(.*)/\$1\$2/" *
  fi
}
check_prefix 10
if [ "$CHK" -ne 0 ]; then
check_prefix 16
fi
if [ "$CHK" -ne 0 ]; then
check_prefix 19
fi

# return success code
echo "result stored to ${EXPORT_TO}"
exit 0
