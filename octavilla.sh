#!/bin/bash

if [[ $# -eq 0 ]]; then
    echo "Tienes que pasar un fichero como argumento"
    exit 0
fi

if [[ ! -f "$1" ]]; then
    echo "$1 no es un fichero"
    exit 0
fi

CMD=$(basename "$0")
ITER=9

# Guias para cortar
# Ancho: 842
#  Alto: 595
if [ $ITER -eq 9 ]; then
    read -r -d '' LINES <<EOF
    0 280.66 moveto 595 280.66 lineto stroke
    0 561.33 moveto 595 561.33 lineto stroke

    198.33 0 moveto 198.33 842 lineto stroke
    396.66 0 moveto 396.66 842 lineto stroke
EOF
elif [ $ITER -eq 8 ]; then
    read -r -d '' LINES <<EOF
    0 210.5 moveto 595 210.5 lineto stroke
    0 421 moveto 595 421 lineto stroke
    0 631.5 moveto 595 631.5 lineto stroke

    297.5 0 moveto 297.5 842 lineto stroke
EOF
elif [ $ITER -eq 4 ]; then
    read -r -d '' LINES <<EOF
    0 421 moveto 595 421 lineto stroke

    297.5 0 moveto 297.5 842 lineto stroke
EOF
fi

read -r -d '' GRID <<EOF
<< /BeginPage
{
    0.7 setgray

    $LINES
}
>> setpagedevice
EOF

SOURCE=$(realpath -- "$1")

DIR="$PWD"

cd $(mktemp -d)

echo "Directorio de trabajo: $PWD"

filename=$(basename -- "$1")
extension="${filename##*.}"
filename="${filename%.*}"

WORKCOPY="in.pdf"
OUTPUT="$DIR/${filename}"

if [[ "$extension" != "pdf" ]]; then
    unoconv -f pdf -o "$WORKCOPY" "$SOURCE"
    if [ $? -ne 0 ]; then
        exit $?
    fi
else
    cp "$SOURCE" "$WORKCOPY"
    OUTPUT="${OUTPUT}_${ITER}"
fi

pages=$(pdfinfo "$WORKCOPY" | grep Pages | awk '{print $2}')

if [ $pages -ne 2 ]; then
    echo "El número de páginas ha de ser 2"
    exit 0
fi

function build_page {
    PAG=""
    for (( c=1; c<=$ITER; c++ )); do
        PAG="$PAG $1"
    done
    pdftk "$WORKCOPY" cat $PAG output "$1.pdf"
    rot=$(pdfinfo "$1.pdf" | grep "Page rot" | awk '{print $3}')
    if [ $rot -ne 0 ]; then
        pdftk "$1.pdf" cat 1-endnorth output "$1_north.pdf"
        mv "$1_north.pdf" "$1.pdf"
    fi

    size=$(pdfinfo "$1.pdf" | grep "Page size" | awk '{print $3, $5}')
    width=$(echo $size | cut -d' ' -f1)
    height=$(echo $size | cut -d' ' -f2)
    pdf2ps "$1.pdf" "$1.ps"
    psnup -W${width} -H${height} -pa4 -${ITER} "$1.ps" "$1_oct.ps"

    if [ $1 -eq 1 ]; then
        cp "$1_oct.ps" "$1_oct.bak.ps"
        echo $GRID > "$1_oct.ps"
        cat "$1_oct.bak.ps" >> "$1_oct.ps"
    fi
    rm "$1.pdf"
    ps2pdf "$1_oct.ps" "$1.pdf"
    rot=$(pdfinfo "$1.pdf" | grep "Page rot" | awk '{print $3}')
    if [ $rot -eq 90 ]; then
        if [ $1 -eq 1 ]; then
            pdftk "$1.pdf" cat 1-endleft output "$1_rotate.pdf"
            mv "$1_rotate.pdf" "$1.pdf"
        else
            pdftk "$1.pdf" cat 1-endright output "$1_rotate.pdf"
            mv "$1_rotate.pdf" "$1.pdf"
        fi
    fi
}

build_page 1
build_page 2

pdftk 1.pdf 2.pdf cat output "${OUTPUT}.pdf"
