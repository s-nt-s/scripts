#!/usr/bin/python3
# -*- coding: utf-8 -*-

import json
import os
import re
import sys
import time
from datetime import date, datetime, timedelta
from unicodedata import normalize
from urllib.parse import urlencode, urljoin

import bs4
import requests

import enchant

url_afraid = "https://freedns.afraid.org/domain/registry/page-%s.html"
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

now = datetime.now().date()
ok_words = dict()
ko_wrods = set()
word_dict = {
    "es": enchant.Dict("es_ES"),
    "en": enchant.Dict("en_US")
}
re_vowel = re.compile(r"[aeiou]", re.IGNORECASE)
re_sp = re.compile(r"\s+")
re_date = re.compile(r'\d+/\d+/\d+')


def get(url, tried=0):
    r = None
    try:
        r = s.get(url)
    except Exception as e:
        if tried > 3:
            raise e from None
        time.sleep(10)
        return get(url, tried=tried + 1)
    soup = bs4.BeautifulSoup(r.text, "lxml")
    return soup


def get_letsencrypt():
    root = "https://crt.sh/?CAName=%25s+Encrypt%25"
    soup = get(root)
    urls = set()
    for a in soup.select("td a"):
        url = urljoin(root, a.attrs["href"])
        caid = url.split("=")[-1]
        url = "https://crt.sh/?iCAID=" + caid + \
            "&exclude=expired&p=1&n=900&Identity="  # + dom, + %.dom
        urls.add(url)
    return urls

urls_letsencrypt = get_letsencrypt()


def count_letsencrypt(dom):
    total = 0
    dates = []
    for url in urls_letsencrypt:
        for d in (dom, '%.' + dom):
            soup = get(url + d)
            for th in soup.findAll("th"):
                txt = re_sp.sub(" ", th.get_text()).strip()
                if txt.startswith("Certificates ("):
                    total = int(txt[14:-1])
            for tr in soup.findAll("tr"):
                tds = tr.findAll("td")
                if len(tds) == 4:
                    _id = tds[0].find("a").attrs["href"]
                    _cn = tds[3].get_text().strip()
                    if _id.startswith("?id=") and _cn.startswith("CN="):
                        txt = tds[1].get_text().strip()
                        create = datetime.strptime(txt, "%Y-%m-%d").date()
                        dates.append(create)
    if total == 0:
        total = len(dates)
    return (total, dates)


def get_lang_word(a):
    langs = set()
    if len(a) < 2:
        return langs
    if not re_vowel.search(a):
        return langs
    if a in ko_wrods:
        return langs
    if a in ok_words.keys():
        return ok_words[a]
    for k, wd in word_dict.items():
        if wd.check(a):
            langs.add(k)
            continue
        for s in wd.suggest(a):
            w = normalize('NFKD', s).encode('ascii', 'ignore')
            if w == a:
                langs.add(k)
    if len(langs) == 0:
        ko_wrods.add(a)
        return langs
    ok_words[a] = langs
    return langs


def get_lang_phrase(*args):
    langs = set()
    for phrase in args:
        for word in phrase.split("-"):
            langs = langs.union(get_lang_word(word))
    if len(langs) == 0:
        return None
    return tuple(langs)


def get_domains(soup):
    doms = []
    for tr in soup.findAll("tr"):
        tds = tr.findAll("td")
        if len(tds) == 4:
            if tds[1].get_text().strip() in ("public", "private"):
                doms.append(Domain(tds))
    return doms


class Domain():
    DEF_ATTR = ("letsencrypt", "create_letsencrypt",
                "langs", "create", "owner")

    @staticmethod
    def from_afraid():
        domains = []
        i = 0
        while True:
            i += 1
            soup = get(url_afraid % i)
            doms = get_domains(soup)
            if len(doms) == 0:
                domains = list(set(domains))
                domains.sort(key=lambda d: d.key)
                return domains
            domains.extend(doms)
        return domains

    @staticmethod
    def load(*args):
        domains = []
        for fl in args:
            ext = fl.split(".")[-1]
            with open(fl, "r") as f:
                if ext == "txt":
                    for l in f.readlines():
                        l = l.strip()
                        if len(l) > 0:
                            domains.append(Domain(tuple(l.split())))
                elif ext == "json":
                    domains.extend([Domain(j) for j in json.load(f)])
        domains = list(set(domains))
        domains.sort(key=lambda d: d.key)
        return domains

    @staticmethod
    def store(fl, domains):
        domains.sort(key=lambda d: d.key)
        ext = fl.split(".")[-1]
        with open(fl, "w") as f:
            if ext == "txt":
                for d in domains:
                    f.write(str(d) + "\n")
            elif ext == "json":
                doms = [d.to_dict() for d in domains]
                json.dump(doms, f, sort_keys=True, indent=4)

    def __init__(self, data):
        if isinstance(data, tuple):
            self.dom = data[3]
            self.public = data[1] == "1"
            self.create = datetime.strptime(data[0], "%Y-%m-%d").date()
            self.hosts = int(data[2])
        elif isinstance(data, dict):
            for k, v in data.items():
                if k.startswith("dt_") and v:
                    k = k[3:]
                    if isinstance(v, str):
                        v = datetime.strptime(v, "%Y-%m-%d").date()
                    else:
                        dts_v = []
                        for i in v:
                            dts = datetime.strptime(i, "%Y-%m-%d").date()
                            dts_v.append(dts)
                        v = dts_v
                setattr(self, k, v)
        else:
            self.dom = data[0].find("a").get_text().strip()
            self.public = data[1].get_text().strip() == "public"
            self.owner = data[2].find("a").get_text().strip()
            self.hosts = int(data[0].find(
                "span").get_text().strip()[1:].split(" ")[0])

            str_create = re_date.search(data[3].get_text()).group()
            self.create = datetime.strptime(str_create, "%m/%d/%Y").date()
        for attr in Domain.DEF_ATTR:
            if attr not in self.__dict__.keys():
                setattr(self, attr, None)

    @property
    def top(self):
        return self.dom[self.dom.rindex(".") + 1:]

    @property
    def name(self):
        return self.dom[:self.dom.rindex(".")]

    @property
    def key(self):
        return tuple(reversed(self.dom.split(".")))

    @property
    def old(self):
        return (datetime.today().date() - self.create).days

    @property
    def recent_letsencrypt(self):
        self.count_letsencrypt()
        recent = 0
        day_limit = 7
        for d in self.create_letsencrypt:
            days = (now - d).days
            if (days) < day_limit:
                recent += 1
        return recent

    def to_dict(self):
        dct = {}
        for k, v in self.__dict__.items():
            if v or isinstance(v, int):
                if isinstance(v, date):
                    k = "dt_" + k
                    v = v.strftime('%Y-%m-%d')
                if isinstance(v, list) and isinstance(v[0], date):
                    k = "dt_" + k
                    str_v = []
                    for i in v:
                        s = i.strftime('%Y-%m-%d')
                        str_v.append(s)
                    v = str_v
                dct[k] = v
        return dct

    def load_langs(self):
        if self.langs is None:
            steps = self.dom.split(".")[:-1]
            steps.append(self.dom.replace(".", ""))
            self.langs = get_lang_phrase(*steps)
        return self.langs

    def is_cool(self):
        if self.dom.count(".") > 1:
            return False
        if self.dom.count("--") > 0:
            return False
        lname = len(self.name)
        if lname < 3:
            return True
        if lname > 14:
            return False
        if self.name.isdigit() and lname < 5:
            return True
        if not re_vowel.search(self.name):
            return False
        if lname < 4 and self.dom.count("-") == 0:
            return True
        if len(self.top) > 4 and not get_lang_word(self.top):
            return False
        if self.load_langs():
            return True
        return False

    def count_letsencrypt(self):
        if self.letsencrypt is None:
            self.letsencrypt, self.create_letsencrypt = count_letsencrypt(
                self.dom)
        if not self.create_letsencrypt:
            self.create_letsencrypt = tuple()
        return self.letsencrypt

    def __hash__(self):
        return hash(self.dom)

    def __eq__(self, other):
        return self.dom == other.dom

    def __str__(self):
        return "%s %s %6s %s" % (self.create, int(self.public), self.hosts, self.dom)
