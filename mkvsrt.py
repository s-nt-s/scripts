#!/usr/bin/python3
import subprocess
import json
import argparse
import tempfile
import sys
from munch import Munch
from functools import lru_cache
from os.path import isfile
import re

re_sp = re.compile(r"\s+")


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
        return "ass"
    if track.codec == "SubRip/SRT":
        return "srt"

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
            srt = ass.rsplit(".", 1)[0]+".srt"
            run_cmd("ffmpeg", "-i", ass, srt)
            s.new_sub = srt

        arr = ["mkvmerge", "-o", self.file+".srt.mkv", "--no-attachments", "-s", "!{}".format(",".join(str(s.id) for s in subs)), self.file]
        for i, s in enumerate(subs):
            s.id = 0
            cmd = '''
                --language {id}:{language_ietf}
                --sub-charset {id}:{encoding}
            '''.format(**s)
            cmd = re_sp.sub(" ", cmd).strip()
            arr.extend(cmd.split())
            if s.get('default_track'):
                arr.extend(["--default-track", "{id}:yes".format(**s)])
            if s.get('forced_track'):
                arr.extend(["--forced-track", "{id}:yes".format(**s)])
            if s.get('track_name'):
                arr.extend(["--track-name", "{id}:{track_name}".format(**s)])
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
