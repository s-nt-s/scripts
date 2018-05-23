#!/usr/bin/python3
# -*- coding: utf-8 -*-

import argparse
import hashlib
import os
import re
from getpass import getpass

import requests

get_ip = re.compile(r" (\d+\.\d+\.\d+\.\d+) ")
not_ch = re.compile(r"ERROR: Address (\d+\.\d+\.\d+\.\d+) has not changed\.")


parser = argparse.ArgumentParser(
    description='Set ip in domains of freedns.afraid.org')
parser.add_argument('--own-dir', action='store_true',
                    help="Move to script's directory")
parser.add_argument("key", type=str, nargs='?',
                    help="Key file", default="freedns.afraid.key")
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
    key = user + "|" + password
    sha1.update(key.encode('utf-8'))
    key = sha1.hexdigest()
    with open(arg.key, "w") as f:
        f.write(key)
else:
    with open(arg.key, "r") as f:
        key = f.read().strip()

url = "http://freedns.afraid.org/api/?action=getdyndns&v=2&sha=" + key
r = requests.get(url)

doms = {}
for l in r.text.strip().split("\n"):
    l = l.strip()
    data = l.split("|")
    if len(data) == 3:
        dom, ip, url = data
        doms[dom] = (ip, url)

keys = sorted(doms.keys())
re_doms = re.compile(r"\b(" + "|".join([re.escape(d) for d in keys]) + r")\b")
done = set()
myip = None

for k in keys:
    if k not in done:
        ip, url = doms[k]
        if ip == myip:
            continue
        r = requests.get(url)
        r = r.text.strip()
        m = not_ch.match(r)
        if m:
            myip = m.group(1)
            continue
        print (r)
        if r.startswith("Updated "):
            done = done.union(set(re_doms.findall(r)))
