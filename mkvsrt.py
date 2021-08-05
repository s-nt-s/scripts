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
import pysubs2

re_sp = re.compile(r"\s+")
TMP = tempfile.mkdtemp()


def get_cmd(*args):
    print("$", *[a if not(" " in a or "!" in a) else "'"+a+"'" for a in args])
    output = subprocess.check_output(args)
    output = output.decode('utf-8')
    return output


def run_cmd(*args):
    print("$", *[a if not(" " in a or "!" in a) else "'"+a+"'" for a in args])
    out = subprocess.call(args)
    return out


def backtwo(arr):
    arr = zip(range(1, len(arr)), arr[1:], arr)
    return reversed(list(arr))


class Sub:
    def __init__(self, file):
        self.file = file

    def load(self, to_type=None):
        subs = pysubs2.load(self.file)
        subs.sort()
        if to_type and not self.file.endswith("."+to_type):
            subs = pysubs2.SSAFile.from_string(subs.to_string(to_type))
            subs.sort()
        flag = len(subs)+1
        while len(subs) < flag:
            flag = len(subs)
            for i, s in reversed(list(enumerate(subs))):
                for o in subs[:i]:
                    if o.text == s.text and o.start <= s.start and o.end >= s.start:
                        del subs[i]
                        break
            for i, s, prev in backtwo(subs):
                if s.text != prev.text and (s.start, s.end) == (prev.start, s.end):
                    prev.text = prev.text + "\n" + s.text
                    del subs[i]
            subs.sort()
        return subs

    def save(self, out):
        if "." not in out:
            out = self.file.rsplit(".", 1)[0]+"."+out
        to_type = out.rsplit(".", 1)[-1]
        if out == self.file:
            out = out+"."+to_type
        subs = self.load(to_type=to_type)
        subs.save(out)
        return out


class Track(DefaultMunch):
    def __init__(self, *args, **kvargs):
        super().__init__(*args, **kvargs)

    @property
    def lang(self):
        return self.language_ietf or self.language

    @property
    def lang_name(self):
        if self.lang in ("es", "spa"):
            return "Español"
        if self.lang in ("ja", "jap"):
            return "Japonés"
        if self.lang in ("en", "eng"):
            return "Inglés"
        return self.lang

    @property
    def file_extension(self):
        if self.codec == "SubStationAlpha":
            return "ssa"
        if self.codec == "SubRip/SRT":
            return "srt"
        if self.codec == "AC-3":
            return "ac3"
        if self.codec == "DTS":
            return "dts"
        if self.codec_id == "A_VORBIS":
            return "ogg"

    @property
    def label_video(self):
        lb = None
        if "H.264" in self.codec:
            lb = "H.264"
        if lb is None:
            return None
        if self.pixel_dimensions:
            lb = "{} ({})".format(lb, self.pixel_dimensions)
        return lb

    @property
    def label_name(self):
        if self.label_video is None and self.file_extension is None:
            return None
        flabel = None if self.file_extension is None else "({})".format(
            self.file_extension)
        if self.track_name is None:
            if self.label_video is not None:
                return self.label_video
            if flabel is None:
                return None
            if self.lang_name is not None:
                return self.lang_name+" "+flabel
            return flabel
        lb = (self.label_video or flabel)
        if lb in self.track_name:
            return None
        return self.track_name+" "+lb


class Mkv:
    def __init__(self, file):
        self.file = file
        self._info = None

    @property
    def info(self):
        if self._info is None:
            js = get_cmd("mkvmerge", "-F", "json", "--identify", self.file)
            js = json.loads(js)
            self._info = DefaultMunch.fromDict(js)
        return self._info

    def mkvextract(self, *args):
        if len(args) > 0:
            run_cmd("mkvextract", "tracks", self.file, *args)

    def extract(self, *tracks):
        outs = []
        for track in tracks:
            if isinstance(track, int):
                track = self.get_track(track)
            if track.file_extension is None:
                raise Exception(
                    "La pista {id} con tipo {type} y formato {codec} no tiene extension".format(**track))
            out = "{0}:{1}/{0}.{2}".format(track.id, TMP, track.file_extension)
            outs.append(out)
        self.mkvextract(*outs)
        return [out.split(":", 1)[-1] for out in outs]

    def safe_extract(self, id):
        trg = {}
        name = self.file.rsplit(".", 1)[0]
        for track in self.tracks:
            if track.file_extension is None:
                continue
            trg[track.id] = track
            out = "{0}:{1}/{0}.{2}".format(track.id, TMP, track.file_extension)
        track = trg.get(id)
        if track is None:
            print("No se puede extraer la pista", id)
            print("Las pistas disponibles son:")
            for _, track in sorted(trg.items(), key=lambda x: x[0]):
                print(track.id, (track.label_name or track.track_name),
                      "->", "{}.{}".format(name, track.file_extension))
            return
        out = "{0}:{1}.{2}".format(track.id, name, track.file_extension)
        self.mkvextract(out)

    @property
    def tracks(self):
        arr = []
        for t in self.info.tracks:
            track = Track()
            track.update(t.properties.copy())
            track.id = t.id
            track.codec = t.codec
            track.type = t.type
            arr.append(track)
        return arr

    def get_track(self, id):
        for t in self.tracks:
            if t.id == id:
                return t

    def mkvpropedit(self, *args):
        if len(args) == 0:
            return
        run_cmd("mkvpropedit", self.file, *args)
        self._info = None

    def mark_tracks(self):
        arr = []
        for s in self.tracks:
            if s.label_name:
                arr.extend("--edit track:{} --set".format(s.number).split())
                arr.append("name="+s.label_name)
        self.mkvpropedit(*arr)

    def fix_lang(self, und):
        if und is None:
            return
        arr = []
        for s in self.tracks:
            if s.language == 'und':
                arr.extend(
                    "--edit track:{} --set language={}".format(s.number, und).split())
        self.mkvpropedit(*arr)

    def convert(self):
        oupput = self.file

        subs = [s for s in self.tracks if s.type ==
                "subtitles" and s.codec != 'SubRip/SRT']
        if len(subs) > 0:
            fls = self.extract(*subs)
            for s, ori in zip(subs, fls):
                s.new_sub = Sub(ori).save("srt")

            oupput = self.file+".srt.mkv"
            # "--no-attachments", "-s", "!{}".format(",".join(str(s.id) for s in subs)), self.file]
            arr = ["mkvmerge", "-o", oupput, self.file]
            for i, s in enumerate(subs):
                cmd = '''
                    --sub-charset 0:UTF-8
                '''.format(**s)  # --sub-charset 0:UTF-8{encoding}
                if s.lang:
                    cmd = cmd+" --language 0:"+s.lang
                cmd = re_sp.sub(" ", cmd).strip()
                arr.extend(cmd.split())
                # if s.get('default_track'):
                #    arr.extend(["--default-track", "0:yes".format(**s)])
                if s.forced_track:
                    arr.extend(["--forced-track", "0:yes".format(**s)])
                if s.track_name:
                    arr.extend(["--track-name", "0:{track_name}".format(**s)])
                arr.append(s.new_sub)
            run_cmd(*arr)

        out = Mkv(oupput)
        out.mark_tracks()
        return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Convierte los subtitulos de a srt")
    parser.add_argument('--und', help='Indioma para pistas und')
    parser.add_argument('--track', type=int, help='Extraer una pista')
    parser.add_argument('file', help='Fichero mkv o subtitulos')
    args = parser.parse_args()
    if not isfile(args.file):
        sys.exit("El fichero no existe")
    if args.file.endswith(".mkv"):
        mkv = Mkv(args.file)
        mkv.fix_lang(args.und)
        mkv = mkv.convert()
        if args.track is not None:
            mkv.safe_extract(args.track)
        sys.exit()
    out = Sub(args.file).save("srt")
    print("Resultado en", out)
