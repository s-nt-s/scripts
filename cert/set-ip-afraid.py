#!/usr/bin/python3
# -*- coding: utf-8 -*-

import bs4
import requests
from bunch import Bunch
import json
import argparse
import os
from unicodedata import normalize
import enchant
import re
from urllib.parse import urlencode, urljoin
import sys
from datetime import datetime
import sys
from getpass import getpass
import hashlib
from urllib.request import urlretrieve
import ipgetter
import requests

parser = argparse.ArgumentParser(description='Set ip in domains of freedns.afraid.org')
parser.add_argument('--own-dir', action='store_true', help="Move to script's directory")
parser.add_argument("key", type=str, nargs='?', help="Key file", default="freedns.afraid.key")
arg = parser.parse_args()

if (arg.own_dir):
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)

key = None
if not os.path.isfile(arg.key):
    user = input("User: ")
    password = getpass("Password: ")
    sha1 = hashlib.sha1()
    key = user+"|"+password
    sha1.update(key.encode('utf-8'))
    key = sha1.hexdigest()
    with open(arg.key, "w") as f:
        f.write(key)
else:
    with open(arg.key, "r") as f:
        key = f.read()

CURRENT_IP = ipgetter.myip()
url = "http://freedns.afraid.org/api/?action=getdyndns&v=2&sha="+key
r = requests.get(url)

for l in r.text.strip().split("\n"):
    l = l.strip()
    data = l.split("|")
    if len(data)==3:
        dom, ip, url = data
        if CURRENT_IP != ip:
            print ("%s from %s to %s" % (dom, ip, CURRENT_IP))
            r = requests.get(url)
            print (r.text.strip())
            

