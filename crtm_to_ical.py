#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
import requests
import os
from icalendar import Calendar, Event
import argparse
from glob import glob
import bs4
from datetime import datetime

parser = argparse.ArgumentParser(description='Crea un calendario con la información del la tarjeta de transporte')
parser.add_argument("out", type=str, help="Directorio de los calendarios")
arg = parser.parse_args()

fechas = re.compile(r"\s*(.*?)\s*:\s*(\d\d-\d\d-\d\d\d\d)\s*")
muletilla = re.compile(r"^Fecha (de )?")

def get_info(tarjeta):
    r = requests.get("https://www.tarjetatransportepublico.es/CRTM-ABONOS/consultaSaldo.aspx")
    soup = bs4.BeautifulSoup(r.text, "lxml")
    data = {
        "ctl00$cntPh$btnConsultar": "Continuar",
        "ctl00$cntPh$dpdCodigoTTP": tarjeta[:3],
        "ctl00$cntPh$txtNumTTP": tarjeta[3:]
    }
    for i in soup.select("input"):
        if "name" in i.attrs and "value" in i.attrs and i.attrs["name"].startswith("__"):
            data[i.attrs["name"]] = i.attrs["value"]
    r = requests.post("https://www.tarjetatransportepublico.es/CRTM-ABONOS/consultaSaldo.aspx", data=data)
    soup = bs4.BeautifulSoup(r.text, "lxml")
    resultado = soup.find("div", attrs={"id" : "ctl00_cntPh_tableResultados"})
    if not resultado or len(resultado.get_text().strip())==0:
        return None
    for tag in resultado.select("*"):
        if tag.name == "br":
            tag.replaceWith("\n")
        else:
            tag.unwrap()
    info = resultado.get_text().strip()
    data = {}
    for label, fecha in fechas.findall(info):
        label = muletilla.sub("", label).lower()
        data[label] = fecha

    if "inicio de validez" in data and "carga" in data and data["carga"] == data["inicio de validez"]:
        del data["carga"]

    if "inicio de validez" in data and "primer uso" in data and data["primer uso"] == data["inicio de validez"]:
        del data["inicio de validez"]
        
    return data
    

for ics in glob(arg.out+"/*.ics"):
    tarjeta = os.path.basename(ics)
    tarjeta, _ = os.path.splitext(tarjeta)
    data = get_info(tarjeta)

    cal = Calendar()
    cal.add('version', '2.0')
    cal.add('prodid', '-//'+tarjeta+'//CRTM//ES')
    cal.add('X-WR-CALNAME','CRTM '+tarjeta)
    cal.add('x-wr-timezone', 'Europe/Madrid')
    
    for label, fecha in data.items():
        dt=datetime.strptime(fecha, "%d-%m-%Y").date()

        event = Event()
        event.add('summary', label.capitalize())
        event.add('dtstart', dt)
        event.add('uid',fecha+"_"+label.replace(" ","_"))

        cal.add_component(event)

    with open(ics, 'wb') as f:
        f.write(cal.to_ical())
