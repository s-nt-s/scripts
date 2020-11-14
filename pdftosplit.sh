#!/bin/bash

if [ ! -f "$1" ]; then
   echo "Depe pasar un pdf como parametro"
   exit 1
fi

SRC=$(realpath "$1")
OUT="$SRC.split.pdf"
DIR=$(pwd)

pages=$(pdfinfo "$SRC" | grep Pages | awk '{print $2}')
size=$(pdfinfo "$SRC" | grep "Page size" | awk '{print $3, $5}')
width=$(echo $size | cut -d' ' -f1)
height=$(echo $size | cut -d' ' -f2)

cd $(mktemp -d)

crp=${height%.*}
crp=$((($crp - 5) / 2))
crp=${crp%.*}

mkdir x

# left, bottom, right and top
pdfjam --keepinfo --outfile x/_a.pdf --trim "0pts ${crp}pts 0pts 0pts" --clip true $SRC
pdfjam --keepinfo --outfile x/_b.pdf --trim "0pts 0pts 0pts ${crp}pts" --clip true $SRC

pdfcrop --margins "5 5 5 5" x/_a.pdf  x/a.pdf
pdfcrop --margins "5 5 5 5" x/_b.pdf x/b.pdf

rm x/_*.pdf

#pdfcrop --hires --noclip --margins "0 0 0 -$crp" $SRC x/a.pdf
#pdfcrop --hires --noclip --margins "0 -$crp 0 0" $SRC x/b.pdf
CAT_PR=""
for (( c=1; c<=$pages; c++ )); do
  CAT_PR="$CAT_PR A${c} B${c}"
done

if [ -d ~/tmp_pdftosplit_borrame/ ]; then
   rm -R ~/tmp_pdftosplit_borrame/
fi
mkdir ~/tmp_pdftosplit_borrame/
mv x/*.pdf ~/tmp_pdftosplit_borrame/
pdftk A=~/tmp_pdftosplit_borrame/a.pdf B=~/tmp_pdftosplit_borrame/b.pdf cat $CAT_PR output ~/tmp_pdftosplit_borrame/c.pdf
gs -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -sOutputFile="$OUT" ~/tmp_pdftosplit_borrame/c.pdf
rm -R ~/tmp_pdftosplit_borrame/

if [ -f "$OUT" ]; then
   echo "$(realpath --relative-to="$DIR" "$OUT")"
fi

