import argparse
from urllib.request import urlopen
from urllib.parse import urljoin
from html.parser import HTMLParser
from http.client import HTTPResponse
from functools import cache
import json
from datetime import datetime
import re
from pathlib import Path
from os import utime


TIME_FIELD = '__time__'


def to_timestamp(s):
    if isinstance(s, dict):
        s = s.get(TIME_FIELD)
    if not isinstance(s, str):
        return None
    return datetime(*map(int, re.findall(r"\d+", s))).timestamp()


@cache
def get_body(url: str) -> str:
    r: HTTPResponse
    with urlopen(url) as r:
        b = r.read()
        txt = b.decode("utf-8", errors="ignore")
        return txt.strip()


@cache
def get_json(url: str) -> dict|list:
    return json.loads(get_body(url))


class LinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.__json_links = set()

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for name, value in attrs:
                if name == "href":
                    self.__json_links.add(value)

    @property
    def links(self):
        return tuple(sorted(self.__json_links))

    @classmethod
    def get_links(cls, url: str):
        links: set[str] = set()
        reader = cls()
        reader.feed(get_body(url))
        for link in reader.links:
            abs = urljoin(url, link)
            links.add(abs)
        return tuple(sorted(links))


def main():
    parser = argparse.ArgumentParser(description="Download json from a url")
    parser.add_argument("--out", type=str, help="Local directory to save")
    parser.add_argument("url", type=str, help="URL tree")
    args = parser.parse_args()

    url = str(args.url).rstrip("/")+"/"
    out = Path(args.out)

    links: list[str] = []
    for lk in LinkExtractor.get_links(url):
        if lk.startswith(url) and lk.endswith(".json"):
            links.append(lk)

    frmt = "[{:"+str(len(str(len(links))))+"d}]"
    for i, lk in enumerate(links, start=-len(links)):
        obj = get_json(lk)
        ntm = to_timestamp(obj)
        rel = out / lk[len(url):]
        pth = rel.resolve()
        pth.parent.mkdir(parents=True, exist_ok=True)

        with open(pth, "w") as f:
            json.dump(obj, f, indent=2)

        if ntm is None:
            print(frmt.format(abs(i)), f"{lk} -> {rel}")
        else:
            print(frmt.format(abs(i)), f"{lk} -> {rel} (time={obj[TIME_FIELD]})")
            utime(pth, (ntm, ntm))


if __name__ == "__main__":
    main()
