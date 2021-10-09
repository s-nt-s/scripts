#!/usr/bin/python3
import subprocess
import json
import argparse
import tempfile
import sys
from munch import Munch, DefaultMunch
from functools import lru_cache
from os.path import isfile, basename, isdir
import re
import pysubs2
from shutil import copyfile, move as movefile

re_sp = re.compile(r"\s+")
TMP = tempfile.mkdtemp()
re_nosub = re.compile(r"www\.newpct\.com")

LANG_ES = ("es", "spa", "es-ES")

def get_cmd(*args, do_print=True):
    if do_print:
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

def copy(source, target):
    if None in (source, target) or source == target:
        return False
    print(source, "->", target)
    copyfile(source, target)
    return True

def move(source, target):
    if None in (source, target) or source == target:
        return False
    print(source, "->", target)
    movefile(source, target)
    return True

def farr(s, *args, **kvargs):
    s = s.format(*args, **kvargs)
    return s.split()

class MyList(list):
    def extend(self, s, *args, **kvargs):
        if isinstance(s, str):
            s = s.format(*args, **kvargs)
            s = s.split()
        elif args or kvargs:
            s = [str(i).format(*args, **kvargs) for i in s]
        super().extend(s)

class Sub:
    def __init__(self, file):
        self.file = file

    def load(self, to_type=None):
        subs = pysubs2.load(self.file)
        subs.sort()
        if to_type and not self.file.endswith("."+to_type):
            subs = pysubs2.SSAFile.from_string(subs.to_string(to_type))
            subs.sort()
        for i, s in reversed(list(enumerate(subs))):
            if re_nosub.search(s.text):
                del subs[i]
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
        if self.lang in LANG_ES:
            return "Español"
        if self.lang in ("ja", "jap"):
            return "Japonés"
        if self.lang in ("en", "eng"):
            return "Inglés"
        if self.lang in ("hi", "hin"):
            return "Hindi"
        if self.lang in ("ko", "kor"):
            return "Coreano"
        label = Mkv.get_lang(self.lang)
        if label:
            return label
        return self.lang

    @property
    def isLatino(self):
        if self.track_name is None or self.lang not in LANG_ES:
            return False
        return "latino" in self.track_name.lower()

    @property
    def file_extension(self):
        if self.codec == "SubStationAlpha":
            return "ssa"
        if self.codec == "SubRip/SRT":
            return "srt"
        if self.codec in ("AC-3", "AC-3 Dolby Surround EX", "E-AC-3"):
            return "ac3"
        if self.codec in ("DTS", "DTS-ES"):
            return "dts"
        if self.codec_id == "A_VORBIS":
            return "ogg"
        if self.codec == "MP3":
            return "mp3"
        if self.codec == "FLAC":
            return "flac"

    @property
    def new_name(self):
        if self.type == "video":
            lb = None
            if "H.264" in self.codec:
                lb = "H.264"
            if "H.265" in self.codec:
                lb = "H.265"
            if lb is None:
                return None
            if self.pixel_dimensions:
                lb = "{} ({})".format(lb, self.pixel_dimensions)
            return lb
        if self.file_extension is None:
            return None
        arr=[self.lang_name]
        if self.forced_track and self.type == "subtitles":
            arr.append("forzados")
        arr.append("("+self.file_extension+")")
        return " ".join(arr)

    def to_dict(self):
        d = dict(self)
        d['new_name'] = self.new_name
        d['file_extension'] = self.file_extension
        d['isLatino'] = self.isLatino
        d['lang'] = self.lang
        d['lang_name'] = self.lang_name
        d['track_name'] = self.track_name
        return d

class Mkv:

    def __init__(self, file, output=None):
        self.file = file
        self.output = output
        self._info = None
        self._ban=None

    @staticmethod
    @lru_cache(maxsize=None)
    def get_lang(lang=None):
        lgs = {}
        langs = get_cmd("mkvmerge", "--list-languages", do_print=False)
        for l in langs.strip().split("\n")[2:]:
            label, cod1, cod2 = map(lambda x: x.strip(), l.split(" |"))
            for cod in (cod1, cod2):
                if cod:
                    lgs[cod]=label
        if lang is not None:
            return lgs.get(lang)
        return lgs


    @property
    def info(self):
        if self._info is None:
            arr = MyList()
            arr.extend("mkvmerge -F json --identify")
            arr.append(self.file)
            js = get_cmd(*arr)
            js = json.loads(js)
            self._info = DefaultMunch.fromDict(js)
        return self._info

    @property
    def ban(self):
        if self._ban is None:
            self._ban = Munch(
                audio=set(),
                subtitles=set(),
                video=set(),
                attachments=set()
            )
        return self._ban

    @property
    def main_lang(self):
        langs=set(LANG_ES)
        for s in self.tracks:
            if s.type=='video':
                if s.language_ietf:
                    langs.add(s.language_ietf)
                if s.language:
                    langs.add(s.language)
        return tuple(sorted(langs))

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
        track = trg.get(id)
        if track is None:
            print("No se puede extraer la pista", id)
            print("Las pistas disponibles son:")
            for _, track in sorted(trg.items(), key=lambda x: x[0]):
                print(track.id, (track.new_name or track.track_name),
                      "->", "{}.{}".format(name, track.file_extension))
            return
        out = "{0}:{1}.{2}".format(track.id, name, track.file_extension)
        self.mkvextract(out)

    @property
    def tracks(self):
        arr = []
        ban = set().union(self.ban.audio, self.ban.subtitles, self.ban.video)
        for t in self.info.tracks:
            if t.id in ban:
                continue
            track = Track()
            track.update(t.properties.copy())
            track.id = t.id
            track.codec = t.codec
            track.type = t.type
            arr.append(track)
        return arr

    @property
    def attachments(self):
        arr=[]
        for a in self.info.attachments:
            if a.id in self.ban.attachments:
                continue
            arr.append(a)
        return arr

    def get_tracks(self, *typeids):
        arr = []
        ids = set()
        tys = set()
        for it in typeids:
            if isinstance(it, int):
                ids.add(it)
            else:
                tys.add(it)
        arr = []
        for t in self.tracks:
            if t.id in ids or t.type in tys:
                arr.append(t)
        return arr

    def mkvpropedit(self, *args):
        if len(args) == 0:
            return
        run_cmd("mkvpropedit", self.file, *args)
        self._info = None

    @property
    def file_output(self):
        if self.output is None:
            return self.file+".merge.mkv"
        return self.output

    def mkvmerge(self, *args):
        if len(args) == 0 or len(args)==1 and args[0] == self.file:
            return
        if self.file not in args:
            args=list(args)
            args.insert(0, self.file)
        run_cmd("mkvmerge", "-o", self.file_output, *args)
        self.file = self.file_output
        self._info = None
        self._ban = None

    def get_order(self, more_audio=None, more_subtitles=None):
        if more_audio is None:
            more_audio = []
        if more_subtitles is None:
            more_subtitles = []
        sort_s = lambda x: x.number
        orde = sorted(self.get_tracks('video'), key=sort_s)
        aux = Munch(
            es_ac3=[],
            mn_ac3=[],
            ot_ac3=[],
            es_otr=[],
            mn_otr=[],
            ot_otr=[],
        )
        for s in self.get_tracks('audio')+more_audio:
            if s.file_extension == "ac3":
                if s.lang in LANG_ES:
                    aux.es_ac3.append(s)
                    continue
                if s.lang in self.main_lang:
                    aux.mn_ac3.append(s)
                    continue
                aux.ot_ac3.append(s)
                continue
            if s.lang in LANG_ES:
                aux.es_otr.append(s)
                continue
            if s.lang in self.main_lang:
                aux.mn_otr.append(s)
                continue
            aux.ot_otr.append(s)
        for a in aux.values():
            orde.extend(sorted(a, key=sort_s))
        aux = Munch(
            es_ful=[],
            es_for=[],
            mn_ful=[],
            mn_for=[],
            ot_ful=[],
            ot_for=[],
        )
        for s in self.get_tracks('subtitles')+more_subtitles:
            if s.forced_track:
                if s.lang in LANG_ES:
                    aux.es_for.append(s)
                    continue
                if s.lang in self.main_lang:
                    aux.mn_for.append(s)
                    continue
                aux.ot_for.append(s)
                continue
            if s.lang in LANG_ES:
                aux.es_ful.append(s)
                continue
            if s.lang in self.main_lang:
                aux.mn_ful.append(s)
                continue
            aux.ot_for.append(s)

        for a in aux.values():
            orde.extend(sorted(a, key=sort_s))

        reorder = False
        newordr = []
        for o, s in enumerate(orde):
            newordr.append("{}:{}".format(s.get('source', 0), s.get('id', 0)))
            if s.number != (o+1) or s.get('source', 0)!=0:
                reorder=True

        if reorder is False:
            return None

        return ",".join(newordr)

    def fix_tracks(self):
        arr = MyList()
        title = basename(self.file)
        title = title.rsplit(".", 1)[0]
        title = title.strip()
        if self.info.container.properties.title != title:
            arr.extend("--edit info --set")
            arr.append("title="+title)
            
        for s in self.tracks:
            if s.new_name and s.new_name!=s.track_name:
                arr.extend("--edit track:{} --set", s.number)
                arr.append("name="+s.new_name)

        self.mkvpropedit(*arr)

        newordr = self.get_order()

        if newordr:
            m = Mkv(self.file)
            m.mkvmerge("--track-order", newordr)
            movefile(m.file, self.file)
            self._info = None
            self._ban = None


    def fix_properties(self, und):
        arr = MyList()
        isUnd = False
        for s in self.tracks:
            if s.language == 'und':
                if und is None:
                    print("# Pista {id} {track_name} ({file_extension}) necesita definir idioma".format(**s.to_dict()))
                    isUnd = True
                else:
                    arr.extend("--edit track:{} --set language={}", s.number, und)
        if isUnd:
            raise Exception("Es necesario definir el parámentro und")
            
        sub_langs={}
        for s in self.get_tracks('subtitles'):
            if s.lang not in self.main_lang:
                continue
            if s.lang not in sub_langs:
                sub_langs[s.lang]=[]
            sub_langs[s.lang].append(s)
        for subs in sub_langs.values():
            if any(s.forced_track for s in subs):
                continue
            forced_done = False
            for s in subs:
                if s.track_name is None:
                    continue
                tn = s.track_name.lower()
                if s.track_name and ("forzados" in tn or "forced" in tn) and not s.forced_track:
                    arr.extend("--edit track:{} --set flag-forced=1", s.number)
                    forced_done = True
            if forced_done is False and len(subs)>0:
                fls = self.extract(*subs)
                for i, (f, s) in enumerate(zip(fls, subs)):
                    lines = len(Sub(f).load("srt"))
                    subs[i]=(lines, s)
                subs=sorted(x for x in subs if x[0]>0)
                if len(subs)>1 and subs[0][0]<(subs[-1][0]/2):
                    arr.extend("--edit track:{} --set flag-forced=1", subs[0][1].number)

        self.mkvpropedit(*arr)

    def convert(self, do_srt=False, do_ac3=False):
        arr = MyList()

        for s in self.get_tracks('audio', 'subtitles'):
            if s.lang and (s.isLatino or s.lang not in self.main_lang):
                latino = " - latino" if s.isLatino else ""
                if s.type == 'subtitles':
                    self.ban.subtitles.add(s.id)
                    print("# RM {file_extension} {id} {track_name} por idioma ({lang}{latino})".format(latino=latino, **s.to_dict()))
                if s.type == 'audio':
                    self.ban.audio.add(s.id)
                    print("# RM {file_extension} {id} {track_name} por idioma ({lang}{latino})".format(latino=latino, **s.to_dict()))

        if do_srt:
            sbs = self.get_tracks('subtitles')
            fls = self.extract(*sbs)
            for f, s in zip(fls, sbs):
                lines = Sub(f).load("srt")
                if len(lines)<1:
                    print("# RM {file_extension} {id} {track_name} por estar vacio".format(**s.to_dict()))
                    self.ban.subtitles.add(s.id)

        c_sub = len(self.get_tracks('subtitles'))
        for a in self.attachments:
            if c_sub==0 or a.get('content_type')!="application/x-truetype-font":
                self.ban.attachments.add(a.id)
                print("# RM {content_type} {id} por tipo o falta de subtitulos".format(**s))

        if self.ban.subtitles:
            nop=",".join(map(str, sorted(self.ban.subtitles)))
            arr.extend("-s !{}", nop)
        if self.ban.audio:
            nop=",".join(map(str, sorted(self.ban.audio)))
            arr.extend("-a !{}", nop)
        if len(self.ban.attachments)==0:
            pass
        if len(self.attachments)==0:
            arr.append("--no-attachments")
        elif len(self.attachments)<len(self.info.attachments):
            sip=",".join(map(str, sorted(a.id for a in self.attachments)))
            arr.extend("-m {}", sip)

        arr.append(self.file)

        si_srt = []
        no_srt = []
        for s in self.get_tracks('subtitles'):
            if s.codec == "SubRip/SRT":
                si_srt.append(s)
            else:
                no_srt.append(s)

        si_ac3 = set()
        for s in self.get_tracks('audio'):
            if s.file_extension == "ac3":
                if s.language_ietf:
                    si_ac3.add(s.language_ietf)
                if s.language:
                    si_ac3.add(s.language)

        cv_aud = []
        for s in self.get_tracks('audio'):
            if s.language_ietf not in si_ac3 and s.language not in si_ac3:
                cv_aud.append(s)

        more_audio = []
        more_subtitles = []
        if do_ac3 and len(cv_aud)>0:
            fls = self.extract(*cv_aud)
            for s, ori in zip(cv_aud, fls):
                out = ori.rsplit(".", 1)[0]+".ac3"
                run_cmd("ffmpeg", "-hide_banner", "-loglevel", "error", "-i", ori, "-acodec", "ac3", out)
                s.new_file = out
            for i, s in enumerate(cv_aud):
                cmd = ""
                if s.lang:
                    cmd = cmd+" --language 0:"+s.lang
                cmd = re_sp.sub(" ", cmd).strip()
                arr.extend(cmd)
                # if s.get('default_track'):
                #    arr.extend(["--default-track", "0:yes".format(**s)])
                if s.default_track:
                    arr.extend("--default-track 0:yes")
                if s.forced_track:
                    arr.extend("--forced-track 0:yes")
                if s.track_name:
                    arr.extend(["--track-name", "0:{track_name}"], **s)

                arr.append(s.new_file)
                more_audio.append(DefaultMunch(
                    lang=s.lang,
                    codec="AC-3",
                    source=len(more_audio)+1,
                    number=1000+i
                ))

        if do_srt and len(si_srt)==0 and len(no_srt)>0:
            fls = self.extract(*no_srt)
            for s, ori in zip(no_srt, fls):
                s.new_file = Sub(ori).save("srt")

            # "--no-attachments", "-s", "!{}".format(",".join(str(s.id) for s in subs)), self.file]
            for i, s in enumerate(no_srt):
                cmd = '''
                    --sub-charset 0:UTF-8
                '''.format(**s)  # --sub-charset 0:UTF-8{encoding}
                if s.lang:
                    cmd = cmd+" --language 0:"+s.lang
                cmd = re_sp.sub(" ", cmd).strip()
                arr.extend(cmd)
                # if s.get('default_track'):
                #    arr.extend(["--default-track", "0:yes".format(**s)])
                if s.forced_track:
                    arr.extend("--forced-track 0:yes")
                if s.track_name:
                    arr.extend(["--track-name", "0:{track_name}"], **s)
                arr.append(s.new_file)
                more_subtitles.append(DefaultMunch(
                    lang=s.lang,
                    forced_track=s.forced_track,
                    source=len(more_audio)+len(more_subtitles)+1,
                    number=2000+i
                ))

        newordr = self.get_order(more_audio, more_subtitles)

        if newordr:
            arr.extend("--track-order " + newordr)

        self.mkvmerge(*arr)
        self.fix_tracks()
        return self.file

    def sub_extract(self):
        isEs = False
        for a in self.get_tracks('audio'):
            if a.lang in LANG_ES:
                isEs = True
        full = None
        forc = None
        for s in self.get_tracks('subtitles'):
            if s.codec == "SubRip/SRT" and s.lang in LANG_ES:
                if s.forced_track:
                    forc = s
                else:
                    full = s
        track = None
        if isEs and forc:
            track = forc
        if track is None and full:
            track  = full
        if track is not None:
            name = self.file.rsplit(".", 1)[0]
            out = "{0}:{1}.{2}".format(track.id, name, track.file_extension)
            self.mkvextract(out)

if __name__ == "__main__":
    langs = sorted(k for k in Mkv.get_lang().keys() if len(k)==2)
    parser = argparse.ArgumentParser("Convierte los subtitulos de a srt")
    parser.add_argument('--und', help='Indioma para pistas und (mkvmerge --list-languages)', choices=langs)
    #parser.add_argument('--must', nargs='*', help='Tipos de pista que ha de contener (por defecto ac3 y srt)', choices=('ac3', 'srt'))
    parser.add_argument('--track', type=int, help='Extraer una pista')
    parser.add_argument('--out', type=str, help='Fichero salida para mkvmerge', default=".")
    parser.add_argument('--do-srt', action='store_true', help='Genera subtitulos SRT si no los hay')
    parser.add_argument('--do-ac3', action='store_true', help='Genera audio ac3 si no lo hay')
    parser.add_argument('file', help='Fichero mkv o subtitulos')
    args = parser.parse_args()
    if not isfile(args.file):
        sys.exit("El fichero no existe")
    if args.file.endswith(".mkv"):
        if isdir(args.out):
            args.out = args.out.rstrip("/")+"/"+basename(args.file)
        if args.file == args.out:
            sys.exit("El fichero de entrada y salida no pueden ser el mismo")
        mkv = Mkv(args.file, args.out)
        mkv.fix_properties(args.und)
        mkv.convert(do_srt=args.do_srt, do_ac3=args.do_ac3)
        mkv.sub_extract()
        if args.track is not None:
            mkv.safe_extract(args.track)
        sys.exit()
    out = Sub(args.file).save(args.out or "srt")
    print("Resultado en", out)
