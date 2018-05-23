#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import re
import sys
from urllib.error import HTTPError
from urllib.parse import urlparse
from urllib.request import urlretrieve

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

titu = guion.sub("_", titu)
podc = guion.sub("_", podc)

podc = mays.sub(r"\1[_ \\-]*\2", podc)
podc = muml.sub(r"\1[_ \\-]*\2", podc)
clean1 = re.compile("^.*?" + podc + "[_ \\-]*", re.IGNORECASE)
clean2 = re.compile("[_ \\-]*" + podc + "[_ \\-]*$", re.IGNORECASE)

titu = clean1.sub("", titu)
titu = fecha.sub("", titu)
titu = clean2.sub("", titu)
titu = trim.sub("", titu)

md = date[5:].split("-")

date = "%X" % int(md[0])
date = date + "." + md[1]

destino = dirc + "/" + date + "-" + titu + ext

print(link)
print(destino)

try:
    urlretrieve(link, destino)
except HTTPError as e:
    if e.code == 404 and len(ext) == 0:
        print (str(e))
    else:
        raise e from None
