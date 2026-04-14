#!/usr/bin/env python3

from datetime import datetime
import os
import re
import sqlite3
import sys

import bs4

import urllib3
from requests import Session
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import requests

urllib3.disable_warnings()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

os.chdir(os.path.dirname(os.path.realpath(sys.argv[0])))

sp = re.compile(r"\s+", re.MULTILINE | re.UNICODE)
con = sqlite3.connect(".notif-web.db", detect_types=sqlite3.PARSE_DECLTYPES)

c = con.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='WEBS'")
r = c.fetchone()
c.close()
if not r or len(r) == 0:
    c = con.cursor()
    c.execute('''CREATE TABLE WEBS (
        URL TEXT PRIMARY KEY NOT NULL,
        SELECTOR TEXT NOT NULL,
        TXT TEXT,
        FCH timestamp
    )''')
    c.close()
    con.commit()


S = Session()
S.headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:54.0) Gecko/20100101 Firefox/54.0',
    "Cache-Control": "no-cache",
    "Pragma": "no-cache",
    "Expires": "Thu, 01 Jan 1970 00:00:00 GMT",
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'es-ES,es;q=0.8,en-US;q=0.5,en;q=0.3',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}


def get(url, selector):
    try:
        response = S.get(url, verify=False)
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        return soup, soup.select(selector)
    except Exception as e:
        print("\nERROR consultando: " + url + "\n" + str(e) + "\n")
    return None, None


cur = con.cursor()
cur.execute('SELECT URL, SELECTOR, TXT from WEBS')
webs = cur.fetchall()
for web in webs:
    soup, nodes = get(web[0], web[1])
    if nodes is None or len(nodes) == 0:
        print(f"{web[1]} no encontrado en {web[0]} {soup}")
        continue
    txt = ''
    for node in nodes:
        txt = txt + " " + node.get_text()
    txt = (sp.sub(" ", txt)).strip()
    if txt == web[2]:
        continue
    print(web[0])
    c = con.cursor()
    c.execute(
        "update WEBS set TXT=?, FCH=? where URL=?",
        (txt, datetime.now().isoformat(sep=" "), web[0])
    )
    c.close()
    con.commit()
