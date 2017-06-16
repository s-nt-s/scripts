#!/usr/bin/python
# -*- coding: utf-8 -*-
import argparse
import requests
import sys
import re
from requests.auth import HTTPBasicAuth
from collections import Counter

parser = argparse.ArgumentParser(description='Abre y cierra puertos en router CG3300CMR')
parser.add_argument('--usuario', help='Usuario del router', default="admin")
parser.add_argument('--clave', help='Clave del router', default="password")
parser.add_argument('--ip', help='Ip local')
parser.add_argument('--abrir', help='Puerto a abrir', type=int)
parser.add_argument('--tipo', help='Tipo del puerto', choices=['TCP/UDP','TCP','UDP'], default="TCP/UDP", action="store")
parser.add_argument('--nombre', help='Nombre para identificar el envio')
parser.add_argument('--borrar', help='Cierra la regla indicada', type=int)
parser.add_argument('--listar', help='Lista las reglas creadas', action="store_true")

arg = parser.parse_args()

re_listado = re.compile(r'forwardingArray\d+\s*=\s*"\s*([^"]+)"')

if not(arg.abrir or arg.listar or arg.borrar):
    sys.exit("Tienes que elegir una de estas opciones: --listar, --borrar, --abrir --help")

auth=HTTPBasicAuth(arg.usuario, arg.clave)

def listado():
    r = requests.post('http://192.168.1.1/RgPortForwardingPortTriggering.htm', auth=auth)
    s = []
    match = re_listado.findall(r.text)
    max_count = len(str(len(match)))
    max_iport = 0
    c = 1
    for i in match:
        sp = i.split(" ")
        ip = sp[-4]
        pt = sp[-5]
        nb = " ".join(sp[0:-9]).replace("&#38;harr;"," ")
        max_iport = max(max_iport,len(ip+pt)+1)
        s.append((c, ip+":"+pt, nb))
        c = c +1
    return s

def print_listado():
    lista = listado()
    if len(lista)==0:
        print "No hay puertos abiertos"
        return
    max_count = len(str(len(lista)))
    max_iport = max(map(lambda x: len(x[1]), lista))

    patron = "%"+str(max_count)+"d - %-"+str(max_iport)+"s %s"
    for i in lista:
        print patron % i

if arg.borrar:
    r = requests.post('http://192.168.1.1/RgPortForwardingPortTriggering.htm', auth=auth, data={
        "RouteSelect": arg.borrar,
        "DeleteService": "Eliminar+servicio"
    })

if arg.listar or arg.borrar:
    print_listado()
    sys.exit(0)

if not arg.ip:
    lista = listado()
    if len(lista)==0:
        sys.exit("Necesita indicar la ip local con --ip")
    ips = map(lambda x: x[1].split(":")[0], lista)
    b = Counter(ips)
    arg.ip, _ = b.most_common(1)[0]

if not arg.nombre:
    arg.nombre = arg.ip + ":" + str(arg.abrir)
else:
    arg.nombre = arg.nombre.replace(" ","_")

ip_split = arg.ip.split(".")

data = {
    "submit_flag": "forwarding_add",
    "Apply": "Aplicar",
    "serflag": "0",
    "service_ip": arg.ip,
    "hidden_portname": "",
    "hidden_port_range": "1",
    "hidden_port_int_start": arg.abrir,
    "hidden_port_int_end": arg.abrir,
    "PortForwardingCustomName": arg.nombre,
    "PortForwardingCustomProtocol": arg.tipo,
    "PortForwardingCustomStartPort": arg.abrir,
    "PortForwardingCustomEndPort": arg.abrir,
    "same_range": "same_range",
    "server_ip1": ip_split[0],
    "server_ip2": ip_split[1],
    "server_ip3": ip_split[2],
    "PortForwardingCustomLocalIP3": ip_split[3]
}

r = requests.post('http://192.168.1.1/RgPortForwardingPortTriggering.htm', data=data, auth=auth)
print_listado()
