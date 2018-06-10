#!/bin/bash

if [[ $# -eq 0 ]] ; then
    echo 'Tienes que pasar un fichero como argumento'
    exit 0
fi

if [[ ! -f "$1" ]]; then
    echo "$1 no es un fichero"
    exit 0
fi

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
    OUTPUT="${OUTPUT}_3x3"
fi

pages=$(pdfinfo "$WORKCOPY" | grep Pages | awk '{print $2}')

if [ $pages -ne 2 ]; then
    echo "El número de páginas ha de ser 2"
    exit 0
fi

function build_page {
    pdftk "$WORKCOPY" cat $1 $1 $1 $1 $1 $1 $1 $1 $1 output "$1.pdf"
    rot=$(pdfinfo "$1.pdf" | grep "Page rot" | awk '{print $3}')
    if [ $rot -ne 0 ]; then
        pdftk "$1.pdf" cat 1-endnorth output "$1_north.pdf"
        mv "$1_north.pdf" "$1.pdf"
    fi
    
    size=$(pdfinfo "$1.pdf" | grep "Page size" | awk '{print $3, $5}')
    width=$(echo $size | cut -d' ' -f1)
    height=$(echo $size | cut -d' ' -f2)
    pdf2ps "$1.pdf" "$1.ps"
    psnup -W${width} -H${height} -pa4 -9 "$1.ps" "$1_oct.ps"
    if [ $1 -eq 1 ]; then
        # Ancho: 841,68
        #  Alto: 595,44
        cp "$1_oct.ps" "$1_oct.bak.ps"
        cat > "$1_oct.ps" <<EOF
<< /BeginPage
{
    0.7 setgray
    
    5 280.56 moveto 590.44 280.56 lineto stroke
    5 561.12 moveto 590.44 561.12 lineto stroke

    198.48 5 moveto 198.48 836.68 lineto stroke
    396.96 5 moveto 396.96 836.68 lineto stroke
}
>> setpagedevice
EOF
        cat "$1_oct.bak.ps" >> "$1_oct.ps"
    fi
    rm "$1.pdf"
    ps2pdf "$1_oct.ps" "$1.pdf"
    
}  

build_page 1
build_page 2

pdftk 1.pdf 2.pdf cat output "${OUTPUT}.pdf"
