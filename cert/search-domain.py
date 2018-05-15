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

url = "https://freedns.afraid.org/domain/registry/page-%s.html"
s = requests.Session()
s.headers = {
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
    "X-Requested-With": "XMLHttpRequest",
}


parser = argparse.ArgumentParser(description='Search in freedns.afraid.org')
parser.add_argument('--refresh', action='store_true')
parser.add_argument('--input', type=str, default="domains-all.json")
parser.add_argument("save", type=str, nargs='?', help="Save result in json")
arg = parser.parse_args()

now = datetime.now().date()
ok_words = set()
ko_wrods = set()
word_dict = (enchant.Dict("es_ES"), ) #enchant.Dict("en_US"))
re_vowel = re.compile(r"[aeiou]", re.IGNORECASE)
re_sp = re.compile(r"\s+")

def get(url):
    r = s.get(url)
    soup = bs4.BeautifulSoup(r.text, "lxml")
    return soup

def get_letsencrypt():
    root = "https://crt.sh/?CAName=%25s+Encrypt%25"
    soup = get(root)
    urls = set()
    for a in soup.select("td a"):
        url = urljoin(root, a.attrs["href"])
        caid = url.split("=")[-1]
        url = "https://crt.sh/?iCAID="+caid+"&exclude=expired&p=1&n=900&Identity=" # + dom, + %.dom
        urls.add(url)
    return urls

urls_letsencrypt = get_letsencrypt()

def count_letsencrypt(dom):
    total = 0
    recent = 0
    day_limit = 7
    for url in urls_letsencrypt:
        for d in (dom, '%.'+dom):
            soup = get(url+d)
            for th in soup.findAll("th"):
                txt = re_sp.sub(" ",th.get_text()).strip()
                if txt.startswith("Certificates ("):
                    total = int(txt[14:-1])
            for tr in soup.findAll("tr"):
                tds = tr.findAll("td")
                if len(tds)==4:
                    _id = tds[0].find("a").attrs["href"]
                    _cn = tds[3].get_text().strip()
                    if _id.startswith("?id=") and _cn.startswith("CN="):
                        txt = tds[1].get_text().strip()
                        create = datetime.strptime(txt, "%Y-%m-%d").date()
                        days = (now - create).days
                        if (days)<day_limit:
                            recent +=1
    return (total, recent)

def is_word(a):
    if len(a)<2:
        return False
    if not re_vowel.search(a):
        return False
    if a in ok_words:
        return True
    if a in ko_wrods:
        return False
    for wd in word_dict:
        if wd.check(a):
            ok_words.add(a)
            return True
        for s in wd.suggest(a):
            w = normalize('NFKD', s).encode('ascii','ignore')
            if w == a:
                ok_words.add(a)
                print (a+ " == "+s)
                return True
    '''
    soup = get("http://dle.rae.es/srv/search?w="+a)
    if soup.find("article"):
        ok_words.add(a)
        return True
    for li in soup.select("li a"):
        w = li.get_text().strip()[:-1]
        w = normalize('NFKD', w).encode('ascii','ignore')
        if w == a:
            ok_words.add(a)
            return True
    '''
    ko_wrods.add(a)
    return False

def is_words(*args):
    for phrase in args:
        flag = True
        for word in phrase.split("-"):
            flag = flag and is_word(word)
        if flag:
            return True
    return False

class Domain(Bunch):

    def __init__(self, tds):
        if isinstance(tds, dict):
            super().__init__(tds)
            self.letsencrypt, self.recent_letsencrypt  = (tds.get("letsencrypt", None), tds.get("recent_letsencrypt", None))
            return
        self.dom = tds[0].find("a").get_text().strip()
        self.public = tds[1].get_text().strip() == "public"
        self.owner = tds[2].find("a").get_text().strip()
        self.old = int(tds[3].get_text().strip().split(" ")[0])
        self.hosts = int(tds[0].find("span").get_text().strip()[1:].split(" ")[0])
        self.letsencrypt = None

    def count_letsencrypt(self):
        if self.letsencrypt is None:
            self.letsencrypt, self.recent_letsencrypt = count_letsencrypt(self.dom)
        return self.letsencrypt
    
    def __hash__(self):
        return hash(self.dom)

    def __eq__(self, other):
        return self.dom == other.dom


def get_domains(soup):
    doms = []
    for tr in soup.findAll("tr"):
        tds = tr.findAll("td")
        if len(tds) == 4:
            if tds[1].get_text().strip() in ("public", "private"):
                doms.append(Domain(tds))
    return doms

def get_domains_from_afraid():
    domains = []
    i = 0
    while True:
        i += 1
        soup = get(url % i)
        doms = get_domains(soup)
        if len(doms)==0:
            return domains
        domains.extend(doms)

if arg.refresh or not os.path.isfile(arg.input):
    print ("Get domains from freedns.afraid.org")
    domains = get_domains_from_afraid()
    with open(arg.input, "w") as f:
        json.dump(domains, f, sort_keys=True, indent=4)
else:
    with open(arg.input, "r") as f:
        domains = [Domain(j) for j in json.load(f)]

res=[]
for d in domains:
    if d.public and d.dom.count(".")<=1:
        spl = d.dom.split(".")
        top = spl[-1]
        if len(top)<4:
            if is_words(*spl[:-1]):
                d.count_letsencrypt()
                print (d.dom)
                res.append(d)

if arg.save:
    with open(arg.save, "w") as f:
        json.dump(res, f, sort_keys=True, indent=4)

