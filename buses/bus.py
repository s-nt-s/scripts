#!/usr/bin/python

import time
import requests
import json
import os
import signal
import sys
import time
import bs4
import re
import os

real=os.path.realpath(sys.argv[0])
os.chdir(os.path.dirname(real))

sp = re.compile(r"\s+", re.MULTILINE|re.UNICODE)

def signal_handler(signal, frame):
    sys.exit(0)
signal.signal(signal.SIGINT, signal_handler)

url1="http://www.cuantotardamiautobus.es/madrid/tiempos.php?t="
cmp1="ids_parada"
url2="http://api.interurbanos.welbits.com/v1/stop/"


def get_json(url):
    response = requests.get(url)
    if response.status_code != 200:
        return []
    js = response.json()
    if "lines" in js:
        return js["lines"]
    return js

with open('bus.json') as data_file:
	buscado = json.load(data_file)
	paradas=buscado.keys()
	if len(sys.argv)>1 and sys.argv[1].isdigit():
		tipo=int(sys.argv[1])
		for p in paradas:
			if "tipo" not in buscado[p] or tipo not in buscado[p]["tipo"]:
				del buscado[p]
	else:
		for p in paradas:
			if "oculto" in buscado[p]:
				del buscado[p]
	paradas=buscado.keys()

buses=[]
for b in buscado:
	for l in buscado[b]["linea"]:
		if l not in buses:
			buses.append(l)

def get_text(n):
	s=sp.sub(" ", n.get_text()).strip()
	return 
		
def add_interurbano(rst,bus):
	r = requests.get("http://www.citram.es/HORARIOS/info.aspx?estacion="+bus)
	soup = bs4.BeautifulSoup(r.text,"lxml")
	trs=soup.select("#dtgHorasPorLinea tr")

	for tr in trs:
		tds=tr.findAll("td")
		j={}
		j["segundos"]=int(get_text(tds[0]).split()[0])*60
		j["linea"]=get_text(tds[2])
		j["destino"]=get_text(tds[3])
		rst.append(j)
	return rst

def tiempos(p, buscado):
	t=time.time()
	param=str(t).replace(".","")
	c=0
	for i in range(0,len(p)):
		param = param + "&" + cmp1 + "[" + str(i) + "]=" + p[i]

	j=get_json(url1+param)
	
	visto=[i["linea"] for i in j]
	paradasI=[]
	busI=[]
	for bus in buses:
		if bus not in visto:
			busI.append(bus)
			for b in buscado:
				if bus in buscado[b]["linea"] and b not in paradasI:
					paradasI.append(b)

	for pI in paradasI:
		lines=get_json(url2+pI)
		for i in lines:
			if i["lineNumber"] in busI and " min" in i["waitTime"]:
				i["linea"]=i["lineNumber"]
				i["segundos"]=int(i["waitTime"].split()[0])*60
				i["destino"]=i["lineBound"]
				i["parada"]=pI
				j.append(i)

	j=sorted(j, key=lambda x: int(x['segundos']))
	rst=[]
	for i in j:
		b=buscado[i["parada"]]
		i["segundos"]=int(i["segundos"])
		if i["linea"] in b["linea"] and i["segundos"]>b["segundos"]:
			if "destino" in b:
				i["destino"]=b["destino"]
			rst.append(i)
	return rst

def get(info,p,b):
	for i in info:
		if i['linea']==b and i['parada']==p:
			return i

def pt(info):
	print ""
	flag=True
	for i in info:
		if i["segundos"]==999999:
			if flag:
				print ""
				flag=False
			m="+20"
		else:
			m=str(i["segundos"]/60)
		msg="%4s %3s -> " + i["destino"]
		print msg % (m,i["linea"])
	print ""
		
while True:
	j=tiempos(paradas, buscado)
	os.system('cls' if os.name == 'nt' else 'clear')
	pt(j)
	time.sleep(20)
