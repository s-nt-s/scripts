#!/usr/bin/python
# -*- coding: utf-8 -*-

import datetime
import os
import re
import sqlite3
import sys

import bs4
import requests

os.chdir(os.path.dirname(sys.argv[0]))

sp = re.compile("\s+", re.MULTILINE | re.UNICODE)
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


def get(url, selector):
    global msg
    try:
        headers = {'Accept-Encoding': None}
        response = requests.get(url, headers=headers)
        soup = bs4.BeautifulSoup(response.text, "html.parser")
        return soup.select(selector)
    except Exception, e:
        print "\nERROR consultando: " + url + "\n" + str(e) + "\n"
    return None


def send(msg):
    cmd = "sudo say \"" + msg + "\" &"
    print cmd
    call(cmd, shell=True)

cur = con.cursor()
cur.execute('SELECT URL, SELECTOR, TXT from WEBS')
webs = cur.fetchall()
for web in webs:
    nodes = get(web[0], web[1])
    if nodes and len(nodes) > 0:
        txt = ''
        for node in nodes:
            txt = txt + " " + node.get_text()
        txt = (sp.sub(" ", txt)).strip()
        if txt != web[2]:
            print web[0]
            c = con.cursor()
            c.execute("update WEBS set TXT=?, FCH=? where URL=?",
                      (txt, datetime.datetime.now(), web[0]))
            c.close()
            con.commit()
