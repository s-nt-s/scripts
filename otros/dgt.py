#!/usr/bin/python3

import bs4
import requests
import signal
import sys
from markdownify import markdownify
import re
import os
import sleekxmpp
import logging
import time

#logging.basicConfig(level=logging.DEBUG, format='%(levelname)-8s %(message)s')

dr = os.path.dirname(os.path.realpath(__file__))

def read(file):
    with open(file, "r") as f:
        for l in f.readlines():
            l=l.strip()
            if l:
                yield l

url = "https://sedeapl.dgt.gob.es/WEB_NOTP_CONSULTA/consultaNota.faces"
nif, examen, nacimiento, void, jid, password, recipient = read(dr+"/dgt.txt")

class SendMsgBot(sleekxmpp.ClientXMPP):
    def __init__(self):
        sleekxmpp.ClientXMPP.__init__(self, jid, password)
        self.recipient = None
        self.msg = None
        self.use_ipv6 = False
        self.auto_reconnect = True
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0004') # Data Forms
        self.register_plugin('xep_0060') # PubSub
        self.register_plugin('xep_0199') # XMPP Ping
        self.add_event_handler("session_start", self.start)

    def start(self, event):
        self.send_presence()
        self.get_roster()
        time.sleep(5)
        self.send_message(mto=self.recipient,
                          mbody=self.msg,
                          mtype='chat')
        self.disconnect(wait=True)

    def run(self, recipient, message):
        self.recipient = recipient
        self.msg = message
        if self.connect():
            self.process(block=True)

s = requests.Session()

re_br = re.compile(r"\s*\n\s*\n\s*")
re_lf = re.compile(r" +$", re.MULTILINE)

def get_text(n):
    soup = bs4.BeautifulSoup(str(n), "html.parser")
    for n in soup.select("*"):
        if not n.get_text().strip():
            n.extract()
    md = markdownify(str(soup))
    md = re_br.sub("\n\n", md)
    md = re_lf.sub("", md)
    return md.strip()

def post():
    r = s.get(url)
    soup = bs4.BeautifulSoup(r.text, "lxml")
    data={}
    form = soup.find("form")
    antes = get_text(form)
    for i in form.findAll("input"):
        name = i.attrs.get("name")
        if name and i.attrs.get("type")!="submit":
            data[name]=i.attrs.get("value")
    data["formularioBusquedaNotas:nifnie"]=nif
    data["formularioBusquedaNotas:fechaExamen"]=examen
    data["formularioBusquedaNotas:clasepermiso"]="B"
    data["formularioBusquedaNotas:fechaNacimiento"]=nacimiento
    data["formularioBusquedaNotas:j_id51"]="Buscar"
    r = s.post(url, data=data)
    soup = bs4.BeautifulSoup(r.text, "lxml")
    form = soup.find("form")
    despues = get_text(form)
    despues = despues.replace(antes, " ")
    despues = despues.strip()
    despues = re_br.sub("\n\n", despues)
    if despues.replace("\n","")==void:
        return None
    return despues+"\n\nFuente: "+url

msg=post()
if msg:
    for r in recipient.split("|||"):
        bot=SendMsgBot()
        bot.run(r, msg)
