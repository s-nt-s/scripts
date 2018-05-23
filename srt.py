#!/usr/bin/python
# -*- coding: utf-8 -*-

import os.path
import re
import sys

reload(sys)
sys.setdefaultencoding('utf8')

if len(sys.argv) != 2 or not os.path.isfile(sys.argv[1]):
    print "Usage: " + sys.argv[0] + " subtitles_file"
    sys.exit(1)

time = re.compile("^\d+:\d+:\d+[.,]\d+ --> \d+:\d+:\d+[.,]\d+$")
sp = re.compile(r"\s+", re.UNICODE)
trim = [
    re.compile(r"([¿¡])\s+", re.UNICODE),
    re.compile(r"\s+([\?!])", re.UNICODE),
    re.compile(r"^(-)\s+", re.UNICODE),
    re.compile(r"\s*(\.\,)\s*$", re.UNICODE)
]


def find_break(l):
    if len(l) > 45:
        m = len(l) / 2
        for c in range(m):
            if l[m + c] == " ":
                return m + c
            if l[m - c] == " ":
                return m - c
    return -1


class Sub:

    def __init__(self, i, time):
        self.l = []
        self.i = i
        self.time = time.replace(".", ",")

    def add(self, l):
        for r in trim:
            l = r.sub(r"\1", l)
        brk = find_break(l)
        if brk == -1:
            self.l.append(l)
        else:
            self.l.append(l[:brk].strip())
            self.l.append(l[brk:].strip())

    def __unicode__(self):
        r = ""
        if i > 1:
            r += "\n"
        r += str(i) + "\n"
        r += self.time + "\n"
        r += "\n".join(self.l)
        return r

    def __str__(self):
        return unicode(self).encode('utf-8')

i = 1

sub = None

with open(sys.argv[1]) as f:
    for l in f.readlines():
        l = sp.sub(" ", l).strip()
        if len(l) == 0:
            continue
        if time.match(l):
            if sub and len(sub.l) > 0:
                print unicode(sub)
                i += 1
            sub = Sub(i, l)
        elif sub:
            sub.add(l)
    if sub and len(sub.l) > 0:
        print unicode(sub)
