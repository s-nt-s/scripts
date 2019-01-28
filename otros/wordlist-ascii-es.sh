#!/bin/bash
curl -Ls http://www.teoruiz.com/lemario/lemario-20101017.txt.gz | zcat | sed  -e 'y/áéíóúü/aeiouu/' -e '/^[a-zA-Z]*$/!d' | perl -nle 'print if m{^[[:ascii:]]+$}' | sed -e '/....*/!d' | sort | uniq
