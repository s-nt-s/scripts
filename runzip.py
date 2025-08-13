#!/usr/bin/env python3
import sys
from os.path import isdir
from pathlib import Path
from zipfile import ZipFile
from tempfile import mkdtemp
from shutil import move
import patoolib

import argparse

parser = argparse.ArgumentParser(
    description='Descomprime de manera recursiva los archivadores encontrados en un directorio'
)
parser.add_argument('ruta', help='Directorio raíz donde se van a buscar los archivadores')
args = parser.parse_args()

if not isdir(args.ruta):
    sys.exit(args.ruta+" no existe")

ROOT = Path(args.ruta)
TEMP = Path(mkdtemp())
print("TEMP:", TEMP, end="\n\n")

def get_zips(root):
    lst = None
    while True:
        r = []
        for e in  ('zip', 'rar'):
            r.extend(root.rglob('*.'+e))
        r = tuple(sorted(r))
        if len(r)==0 or (lst == r):
            break
        lst = r
        for i in r:
            yield i

def unzip(zp, dr):
    patoolib.extract_archive(str(zp), outdir=str(dr), verbosity=-1)
    '''
    ext = zp.suffix.lstrip(".").lower()
    if ext == "zip":
        with ZipFile(zp, 'r') as z:
            z.extractall(dr)
    elif ext == "rar":
        with RarFile(zp, 'r') as r:
            r.extractall(dr)
    else:
        raise Exception(ext+" no reconocida")
    '''

    ch = list(dr.iterdir())
    if len(ch)==1 and (ch[0].name+zp.suffix)==zp.name:
        return ch[0]
    name = zp.name.rsplit(".", 1)[0]
    dr = dr / name
    dr.mkdir()
    for i in ch:
        move(str(i), str(dr))
    return dr
    

for count, zp in enumerate(get_zips(ROOT)):
    dr = TEMP / str(count+1)
    dr.mkdir()
    uz = unzip(zp, dr)
    p = zp.parent
    hjs = list(i.name for i in p.iterdir())
    rnm = False
    while uz.name in hjs:
        rnm = True
        uz.rename(str(uz)+"_")
        uz = Path(str(uz)+"_")
    t = p / uz.name
    if (str(t)+zp.suffix) == str(zp):
        print("[OK]", zp)
    elif rnm:
        print("[RN]", zp, "->", t)
    else:
        print("[MV]", zp, "->", t)
    move(uz, t)
    zp.unlink()
    
