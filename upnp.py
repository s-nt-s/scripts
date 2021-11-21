#!/usr/bin/env python3

import miniupnpc
from munch import Munch
import sys
import re

re_ip = re.compile(r"\b((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(\.|$)){4}\b")
re_nb = re.compile(r"^-?\d+$")

class Rule:
    def __init__(self, protocol=None, port=None, addr=None, dest=None, description=None):
        self.protocol = protocol
        self.port = port
        self.addr = addr
        self.dest = dest
        self.description = description

    def __str__(self):
        return "{protocol}:{port} -> {addr}:{dest} {description}".format(**self.__dict__)

    def fix(self, addr=None):
        if self.protocol is None:
            self.protocol = 'TCP'
        else:
            self.protocol = self.protocol.upper()
        if self.port is not None and self.dest is None:
            self.dest = self.port
        if self.addr is None:
            self.addr = addr
        if r.description is None:
            r.description = 'upnp.py {}'.format(r.port)
        else:
            self.description.strip()

class Upnp:
    def __init__(self):
        self.u = miniupnpc.UPnP()
        self.u.discoverdelay = 200
        self.u.discover()
        self.u.selectigd()

    @property
    def lanaddr(self):
        return self.u.lanaddr

    def get_ports(self):
        i = -1
        while True:
            i += 1
            p = self.u.getgenericportmapping(i)
            if p is None:
                break
            port, protocol, (toAddr, toPort), desc, x, y, z = p
            yield Rule(
                protocol=protocol,
                port=port,
                addr=toAddr,
                dest=toPort,
                description=desc
            )

    def add_port(self, r):
        r.fix(self.lanaddr)
        self.u.addportmapping(
            r.port,
            r.protocol,
            r.addr,
            r.dest,
            r.description,
            ''
        )
        return r


    def del_port(self, r):
        r.fix(self.lanaddr)
        self.u.deleteportmapping(abs(r.port), r.protocol)

    def add_rule(self, r):
        if r.port > 0:
            self.add_port(r)
        else:
            self.del_port(r)

if __name__ == "__main__":
    u = Upnp()
    r = Rule()
    for a in sys.argv[1:]:
        if re_nb.match(a):
            a = int(a)
            if r.port is None:
                r.port = a
            else:
                r.dest = a
        elif re_ip.match(a):
            r.addr = a
        elif a.upper() in ('TCP', 'UDP'):
            r.protocol = a
        else:
            r.description = (r.description or "") + " " + a

    if r.port is not None:
        u.add_rule(r)

    for p in u.get_ports():
        print(str(p))
