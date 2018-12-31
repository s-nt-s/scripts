#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys
import requests

url="https://my.freenom.com/includes/domains/fn-available.php?domain="
flag=False
words=sys.argv[1:]
tdl = None

if words[0].startswith("."):
    tdl = words.pop(0)

for a in sys.argv[1:]:
    ok=set()
    r = requests.get(url+a)
    r = r.json()
    for d in r['free_domains']:
        if d['type']=="FREE" and d['status']=="AVAILABLE" and (tdl is None or tdl == d['tld']):
            ok.add(a+d['tld'])
    if ok:
        if flag:
            print("")
        print("\n".join(sorted(ok)))
        flag = True

