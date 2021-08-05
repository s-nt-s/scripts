#!/usr/bin/python3
import subprocess
import json
import argparse
import tempfile
import sys
from munch import Munch, DefaultMunch
from functools import lru_cache
from os.path import isfile
import re
import pysrt

re_sp = re.compile(r"\s+")
re_rem = (
    re.compile(r"</?font[^>]*>", re.IGNORECASE),
    re.compile(r"{\*\\[^}]*}"),
    re.compile(r"\bm [\-\d\.]+ [\-\d\.]+( l [\-\d\.]+ [\-\d\.]+( [\-\d\.]+)*)+")
)
re_tag1 = re.compile(r"<([^/\s*>]+)( [^>]*)?>(\s*)</\1>")
re_tag2 = re.compile(r"</([^>]+)>(\s*)<\1>")

def read(file):
    with open(file, "r") as f:
        return f.read()

def write(file, txt):
    with open(file, "w") as f:
        f.write(txt)

def get_cmd(*args):
    print("$", *[a if not(" " in a or "!" in a) else "'"+a+"'" for a in args])
    output = subprocess.check_output(args)
    output = output.decode('utf-8')
    return output

def run_cmd(*args):
    print("$", *[a if not(" " in a or "!" in a) else "'"+a+"'" for a in args])
    out = subprocess.call(args)
    return out

def get_info(file):
    output = get_cmd("mkvmerge", "-F", "json", "--identify", file)
    js = json.loads(output)
    return Munch.fromDict(js)

def get_extension(track):
    if track.codec == "SubStationAlpha":
        return "ssa"
    if track.codec == "SubRip/SRT":
        return "srt"

def clean_srt(txt):
    txt = re.sub(r"\\h", " ", txt)
    txt = re.sub(r"  +", " ", txt)
    for r in re_rem:
        txt = r.sub("", txt)
    txt = re_tag1.sub(r"\3", txt)
    txt = re_tag2.sub(r"\2", txt)
    txt = re.sub(r"\\h", " ", txt)
    txt = re.sub(r"^ +", "", txt, flags=re.MULTILINE)
    #txt = txt.replace("{\\an8}\n", "{\\an8}")
    return txt

def convert_sub(ass):
    srt = ass.rsplit(".", 1)[0]+".srt"
    run_cmd("dos2unix", ass)
    txt = read(ass)
    txt = re.sub(r"\\N(\\N)+", r"\\N", txt)
    write(ass, txt)
    run_cmd("ffmpeg", "-i", ass, "-c:s", "srt", srt+".tmp.srt")
    run_cmd("dos2unix", srt)
    txt = read(srt+".tmp.srt")
    txt = clean_srt(txt)
    write(srt, txt)
    sub = pysrt.open(srt)
    dl = []
    def skey(s):
        return (s.text, s.start.seconds, s.end.seconds)
    def eq(s1, s2):
        return skey(s1) == skey(s2)
    flag = len(sub)+1
    while len(sub)<flag:
        flag = len(sub)
        visto = set()
        rm = set()
        for i, s in enumerate(sub):
             key = skey(s)
             if key in visto:
                rm.add(i)
             visto.add(key)
        for i in sorted(rm, reverse=True):
            del sub[i]
        for i, p, s in reversed(list(zip(range(1, len(sub)), sub, sub[1:]))):
            if s.text == p.text:
                p.end = s.end
                del sub[i]
        for i, s in reversed(list(enumerate(sub))):
            if s.text.strip() in ("{\\an8}", ""):
                del sub[i]

        if len(sub)==flag:
            for i, p, s in reversed(list(zip(range(1, len(sub)), sub, sub[1:]))):
                if s.text != p.text and (s.start.seconds, s.end.seconds) == (p.start.seconds, p.end.seconds):
                    if p.text.startswith("{\\an8}") and s.text.startswith("{\\an8}"):
                        s.text = s.text[6:]
                    elif "{\\an8}" in s.text or "{\\an8}" in p.text:
                        continue
                    p.text = p.text+"\n"+s.text
                    del sub[i]
        if len(sub)==flag:
            text = {}
            for i, s in enumerate(sub):
                 text[s.text] = text.get(s.text, [])+[(i, s)]
            for ss in text.values():
                for ((_, p), (i, s)) in reversed(list(zip(ss, ss[1:]))):
                    if p.end.seconds >= s.start.seconds and (p.start.seconds < s.start.seconds):
                        p.end.seconds = s.end.seconds
                        del sub[i]
    bs = 0
    for i, s in enumerate(sub):
        if s.text.startswith("<b>"):
            bs = bs + 1
        s.index = i + 1
    if (bs/len(sub))>0.8:
        for s in sub:
            s.text = re.sub(r"</?b>", "", s.text)
    sub.save(srt)
    txt = read(srt)
    txt = clean_srt(txt)
    write(srt, txt)
    return srt

class Mkv:
    def __init__(self, file):
        self.file = file
        self.info = get_info(self.file)

    @property
    @lru_cache(maxsize=None)
    def work(self):
        return tempfile.mkdtemp()

    def extract(self, *tracks):
        outs = []
        for track in tracks:
            if isinstance(track, int):
                track = self.get_track(track)

            if track.extension is None:
                raise Exception("La pista {id} con tipo {type} y formato {codec} no tiene extension".format(**track))
            out = "{0}:{1}/{0}.{2}".format(track.id, self.work, track.extension)
            outs.append(out)
        run_cmd("mkvextract", "tracks", self.file, *outs)
        return [out.split(":", 1)[-1] for out in outs]

    @property
    @lru_cache(maxsize=None)
    def tracks(self):
        arr = []
        for t in self.info.tracks:
            track = t.properties.copy()
            track.id = t.id
            track.codec = t.codec
            track.extension = get_extension(track)
            track.type = t.type
            arr.append(track)
        return arr


    def get_track(self, id):
        for t in self.tracks:
            if t.id == id:
                return t

    def convert(self):
        subs = [s for s in self.tracks if s.type == "subtitles" and s.codec!='SubRip/SRT']
        if len(subs)==0:
            return False

        ass = self.extract(*subs)
        for s, ass in zip(subs, ass):
            s.new_sub = convert_sub(ass)

        arr = ["mkvmerge", "-o", self.file+".srt.mkv", "--no-attachments", "-s", "!{}".format(",".join(str(s.id) for s in subs)), self.file]
        for i, s in enumerate(subs):
            cmd = '''
                --language 0:{language_ietf}
                --sub-charset 0:UTF-8
            '''.format(**s) # --sub-charset 0:UTF-8{encoding}
            cmd = re_sp.sub(" ", cmd).strip()
            arr.extend(cmd.split())
            if s.get('default_track'):
                arr.extend(["--default-track", "0:yes".format(**s)])
            if s.get('forced_track'):
                arr.extend(["--forced-track", "0:yes".format(**s)])
            if s.get('track_name'):
                arr.extend(["--track-name", "0:{track_name}".format(**s)])
            arr.append(s.new_sub)
        run_cmd(*arr)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Convierte los subtitulos de un mkv a srt")
    parser.add_argument('mkv', help='Fichero mkv')
    args = parser.parse_args()
    if not(isfile(args.mkv) and args.mkv.endswith(".mkv")):
        sys.exit("Fichero no valido "+args.mkv)

    mkv = Mkv(args.mkv)
    mkv.convert()
