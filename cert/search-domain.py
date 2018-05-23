#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import re
import sys
from datetime import datetime
from unicodedata import normalize
from urllib.parse import urlencode, urljoin

import bs4
import requests
from bunch import Bunch

import enchant
from domain import Domain

z
parser = argparse.ArgumentParser(description='Search in freedns.afraid.org')
parser.add_argument('--refresh', action='store_true')
parser.add_argument('--input', type=str, default="domains-all.txt")
parser.add_argument("out", type=str, nargs='?', help="Save result in json")
arg = parser.parse_args()

if arg.refresh or not os.path.isfile(arg.input):
    print ("Get domains from freedns.afraid.org")
    domains = Domain.from_afraid()
    Domain.store(arg.input, domains)
    print ("%s domains found" % len(domains))
else:
    domains = Domain.load(arg.input)

error = None
res = []
for d in domains:
    if d.public and d.old > 7 and d.is_cool():
        try:
            if d.recent_letsencrypt < 20:
                print (d.dom)
                res.append(d)
        except Exception as e:
            error = e
            break

if arg.out:
    Domain.store(arg.out, res)

Domain.store("domains-all.json", domains)

if error:
    raise error from None
