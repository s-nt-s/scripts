#!/usr/bin/python3
# -*- coding: utf-8 -*-

import bs4
import requests
import sys
import re

install = len(sys.argv)>1 and sys.argv[1]=="--install"

re_ban = re.compile(r"\b(not-working\.png|speed-slow\.png|emulator|game server|desktop companion|GPE)\b", re.IGNORECASE)

r = requests.get("http://www.raspberryconnect.com/raspbian-packages-list/item/65-raspbian-games")
soup = bs4.BeautifulSoup(r.content, "lxml")

def get_info(li):
    for img in li.findAll("img"):
        img.replaceWith(img.attrs["src"])
    return li.get_text().strip()

all_games = [(h3.get_text().strip(), h3.find_parent("li"))  for h3 in soup.select("li h3")]

ban_game = set("python-soya balazar balazarbrothers xabacus xmabacus xmpuzzles xpuzzles".split())
dont_like = set("amor 3dchess filler uligo gpe-tetris gpe-othello gpe-lights gpe-go gsoko orbital-eunuchs-snipe robotfindskitten yics emacs-chess holdingnuts bastet bb bastet dizzy xscreensaver-screensaver-dizzy bambam ktuberling".split())
ban_game = ban_game.union(dont_like)
single_game = set()
dash_game = set()
for g, li in all_games:
    info = get_info(li)
    if re_ban.search(info):
        ban_game.add(g)
        continue
    if "-" in g:
        dash_game.add(g)
    else:
        single_game.add(g)

for g in dash_game:
    p, _ = g.split("-", 1)
    if p in ban_game:
        ban_game.add(g)
        continue
    if p in single_game:
        ban_game.add(g)
        continue

dash_game = dash_game - ban_game - single_game
single_game = single_game - ban_game


if install:
    print ("sudo apt install " + " ".join(sorted(single_game)))
else:
    print ("sudo apt purge " + " ".join(sorted(ban_game)))
sys.exit()
