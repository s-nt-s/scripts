#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
from urllib.parse import urlparse
import os
from urllib.request import urlretrieve
import re

guion = re.compile(r"__+")
fecha = re.compile(r"[_ \-]*\d\d[/_]\d\d[/_]\d\d[_ \-]*$")
trim = re.compile(r"^[_ \-]|[_ \-]$")
mays = re.compile(r"([a-z0-9])([A-Z])")
muml = re.compile(r"([0-9])([a-z])")

link = sys.argv[1]
dirc = sys.argv[2]
date = sys.argv[3]
podc = sys.argv[4]
titu = sys.argv[5]

path = urlparse(link).path
ext = os.path.splitext(path)[1]

titu = guion.sub("_",titu)
podc = guion.sub("_",podc)

podc=mays.sub(r"\1[_ \\-]*\2",podc)
podc=muml.sub(r"\1[_ \\-]*\2",podc)
clean = re.compile("^.*"+podc+"[_ \\-]*", re.IGNORECASE)

titu = clean.sub("",titu)
titu = fecha.sub("",titu)
titu = trim.sub("",titu)

date=date[5:].replace("-",".")

destino=dirc+"/"+date+"-"+titu+ext

print(destino)

urlretrieve(link, destino)
