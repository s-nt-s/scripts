from io import TextIOWrapper
import os
from fcntl import flock, LOCK_EX, LOCK_UN
import subprocess
import sys
from typing import Tuple
from functools import cached_property, cache
import re

TARGET = "/etc/hosts"
SECTIONS = ("SSID", "MAC", "VPN", "VPN_DNS")
re_ip = re.compile(r"^\d+\.\d+\.\d+\.\d+\s+(\S+)")


def run(*args):
    if len(args) == 1 and ' ' in args[0]:
        return run(*args[0].split())
    r = subprocess.run(args, capture_output=True, text=True)
    return r.stdout


def runln(*args):
    for ln in run(*args).strip().split("\n"):
        ln = ln.strip()
        if len(ln):
            yield ln


class Data:
    @cached_property
    def ssid(self) -> Tuple[str]:
        try:
            return tuple(sorted(run('iwgetid -r').strip().split()))
        except subprocess.CalledProcessError:
            return tuple()

    @cached_property
    def default_route(self) -> Tuple[str]:
        try:
            ips_route = set()
            for ln in runln('ip route show match 0/0'):
                spl = ln.split()
                if spl[0] == "default":
                    ips_route.add(spl[2])
            return tuple(sorted(ips_route))
        except subprocess.CalledProcessError:
            return tuple()

    @cached_property
    def mac(self) -> Tuple[str]:
        try:
            macs = set()
            for ln in runln('ip neigh'):
                spl = ln.split()
                if spl[0] in self.default_route:
                    macs.add(spl[4])
            return tuple(sorted(macs))
        except subprocess.CalledProcessError:
            return tuple()

    @cached_property
    def vpn(self) -> Tuple[str]:
        try:
            vpns = set()
            for ln in runln('nmcli -g NAME,TYPE connection show --active'):
                spl = ln.split(":")
                if spl[1] == 'vpn':
                    vpns.add(spl[0])
            return tuple(sorted(vpns))
        except subprocess.CalledProcessError:
            return tuple()

    @cache
    def get_dns(self, vpn):
        try:
            for ln in runln('nmcli', 'connection', 'show', vpn):
                spl = re.split(r":\s+", ln)
                if spl[0] == "ipv4.dns":
                    return tuple(spl[1].strip().split(","))
        except subprocess.CalledProcessError:
            return tuple()

    @cache
    def get_ip(self, dom, *dnss):
        for dns in dnss:
            pass


def lock_file(file: TextIOWrapper):
    flock(file.fileno(), LOCK_EX)


def unlock_file(file: TextIOWrapper):
    flock(file.fileno(), LOCK_UN)


def get_section(config_zone: int, line: str, d: Data):
    if config_zone != 1:
        return None
    spl = line.split()
    if len(spl) < 3 or not line.startswith("##"):
        return None
    sec = spl[1]
    if spl[1] not in SECTIONS:
        return None
    val = spl[2]
    if sec == "SSID" and val in d.ssid:
        return sec, val
    if sec == "MAC" and val in d.mac:
        return sec, val
    if sec == "VPN" and val in d.vpn:
        return sec, val
    if sec == "VPN_DNS" and val in d.vpn and d.get_dns(val):
        return sec, val


def update_hosts_file(d: Data):
    section = None

    with open(TARGET, 'r') as file: #+') as file:
        lock_file(file)  # Bloquea el archivo

        lines = file.readlines()
        config_zone = 0
        comment = 1

        new_lines = []

        for line in lines:
            line = line.rstrip()
            if line.startswith("####"):
                comment = 1
                config_zone = 1 - config_zone
                new_lines.append(line)
                continue

            is_section = get_section(config_zone, line, d)

            if is_section is not None:
                section = tuple(is_section)
                comment = 0
                new_lines.append(line)
                continue

            if config_zone == 1 and line.startswith("#") and comment == 0:
                new_line = line[1:].lstrip()
                if section and section[0] == "VPN_DNS":
                    m = re_ip.search(new_line)
                    if m:
                        new_ip = d.get_ip(m.group(1), d.get_dns(section[1]))

                new_lines.append(new_line)
                continue

            if config_zone == 1 and not line.startswith('#') and comment == 1:
                new_lines.append('# ' + line)
                continue

            new_lines.append(line)

        #file.seek(0)
        #file.writelines("\n".join(new_lines))
        #file.truncate()

        unlock_file(file)  # Libera el archivo después de actualizar
    print("\n".join(new_lines))


def create_symlinks(script_path):
    file_name = os.path.basename(script_path)
    real_path = os.path.realpath(script_path)
    cmd = os.path.splitext(file_name)[0]
    link1 = f"/etc/network/if-up.d/{cmd}"
    link2 = f"/etc/network/if-post-down.d/{cmd}"
    os.symlink(real_path, link1)
    os.symlink(real_path, link2)
    print("Now you can do custom zones in", TARGET, "like that:")
    print('''
#### HOME
##
## SSID WIFIA64E
##  MAC c4:05:20:32:b8:4b
##
#
# 192.168.1.30    external.domain.com
#
####
    ''')
    print("# 192.168.1.30    external.domain.com")
    print("will be uncommented when you are connected to WIFIA64E by WIFI or a router with mac c4:05:20:32:b8:4b")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        create_symlinks(__file__)
        sys.exit(0)

    d = Data()
    print("ssid", *d.ssid)
    print("default_route", *d.default_route)
    print("mac", *d.mac)
    for vpn in d.vpn:
        print("vpn", vpn, d.get_dns(vpn))
    update_hosts_file(d)