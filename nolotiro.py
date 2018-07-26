#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
from urllib.parse import urljoin

import bs4
import html2text
import requests


default_headers = {
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

breakline = re.compile(r"[\n]{3,}")


def rel_to_abs(node, attr, root):
    if attr in node.attrs:
        node.attrs[attr] = urljoin(root, node.attrs[attr])


def soup_to_abs(soup, root):
    for a in soup.findAll("a"):
        rel_to_abs(a, "href", root)
    for a in soup.findAll(["img", "frame", "iframe"]):
        rel_to_abs(a, "src", root)
    for a in soup.findAll("from"):
        rel_to_abs(a, "action", root)


class Bubble:

    def __init__(self, api, other, div):
        self.other = other
        self.me = "bg-bubble-me" in div.attrs["class"]
        self.time = div.find("time").attrs["datetime"]
        div.find("time").extract()
        self.text = html2text.html2text(str(div)).strip()
        self.text = breakline.sub(r"\n\n", self.text)


class Thread:

    def __init__(self, api, tr):
        self.api = api
        self.unread = "unread" in tr.attrs.get("class", "")
        a = tr.select("td.mail-subject a")[0]
        self.url = a.attrs["href"]
        self.sender = tr.select("td.sender a")[0].get_text().strip()
        self.subject = a.get_text().strip()
        self.time = tr.find("time").attrs["datetime"]

    def bubbles(self):
        s = self.api.get(self.url)
        for div in s.select("div.bubble"):
            yield Bubble(self.api, self.sender, div)

    def reply(self, text):
        s = self.api.get(self.url)


class NoLoTiro:

    def __init__(self, email, password):
        self.s = requests.Session()
        self.s.headers = default_headers
        self.root = "https://nolotiro.org/"
        soup = self.get("https://nolotiro.org/es/user/login")
        form = soup.find("form")
        data = {}
        for n in form.findAll("input"):
            if "name" in n.attrs:
                data[n.attrs["name"]] = n.attrs.get("value", None)
        data["user[email]"] = email
        data["user[password]"] = password
        self.get(form.attrs["action"], data)

    def get(self, url, data=None):
        url = urljoin(self.root, url)
        if data is None:
            r = self.s.get(url)
        else:
            r = self.s.post(url, data=data)
        s = bs4.BeautifulSoup(r.content, "lxml")
        soup_to_abs(s, url)
        return s

    def threads(self):
        soup = self.get("https://nolotiro.org/es/conversations")
        for tr in soup.select("table.mail-list tbody tr"):
            yield Thread(self, tr)

n = NoLoTiro()
for t in n.threads():
    for b in t.bubbles():
        print (b.text)
        print ("------")
