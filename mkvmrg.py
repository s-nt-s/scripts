#!/usr/bin/python3
import subprocess
import json
import argparse
import tempfile
import sys
from munch import Munch, DefaultMunch
from functools import lru_cache
from os.path import isfile, basename, dirname, realpath
from os import getcwd, chdir
import re
import pysubs2
import codecs
from chardet import detect
from itertools import zip_longest
import xmltodict

re_sp = re.compile(r"\s+")
TMP = tempfile.mkdtemp()
re_nosub = re.compile(r"\bnewpct(\d+)?\.com|\baddic7ed\.com")
re_track = re.compile(r"^(\d+):.*")
re_doblage = re.compile(r"doblaje.*((?:19|20)\d\d+)", re.IGNORECASE)

LANG_ES = ("es", "spa", "es-ES")

def get_encoding_type(file):
    with open(file, 'rb') as f:
        rawdata = f.read()
    return detect(rawdata)['encoding']

def to_utf8(file: str) -> str:
    enc = get_encoding_type(file)
    if enc in ("utf-8", "ascii", "UTF-8-SIG"):
        return file
    
    n_file = TMP + "/" + basename(file)
    while n_file == file:
        n_file = n_file + "." + n_file.split(".")[-1]
    with open(file, 'r', encoding=enc) as s:
        with open(n_file, 'w', encoding='utf-8') as t:
            text = s.read()
            t.write(text)
    print("# MV", file, "({}) -> ({})".format(enc, get_encoding_type(n_file)), n_file)
    return n_file

def get_title(file: str) -> str:
    year = None
    capi = None
    title = basename(file)
    title = title.rsplit(".", 1)[0]
    title = title.strip()
    if re.match(r"^\d+(x\d+)?$", title):
        capi = title
        title = basename(dirname(realpath(file)))
    mtc = re.match(r"(19\d\d|20\d\d)[\s\-]+(.+)", title)
    if mtc:
        year = mtc.group(1)
        title = mtc.group(2).strip()
    if capi:
        title = title + " " + capi
    if year:
        title = title + " ({})".format(year)
    return title


def print_cmd(*args: str):
    arr = []
    for index, a in enumerate(args):
        if " " in a or "!" in a:
            a = "'" + a + "'"
        if args[0] == "mkvpropedit" and a == "--edit":
            a = "\\\n  --edit"
        if args[0] == "mkvmerge" and index > 1:
            if a == "--track-order":
                a = "\\\n  " + a
            elif args[index - 2] == "-o" and "--title" not in args:
                a = "\\\n  " + a
            elif args[index - 2] == "--title":
                a = "\\\n  " + a
            elif isfile(args[index - 1]) and a!="--title":
                a = "\\\n  " + a
            elif a.startswith("--") and index>0 and index<len(args)-1 and not a=="--sub-charset":
                m1 = re_track.match(args[index-1])
                m2 = re_track.match(args[index+1])
                if m1:
                    m1 = int(m1.group(1))
                if m2:
                    m2 = int(m2.group(1))
                if m2 is not None and m2!=m1:
                    a = "\\\n  " + a
        arr.append(a)
    print("$", *arr)


def get_cmd(*args: str, do_print: bool = True, **kargv) -> str:
    if do_print:
        print_cmd(*args)
    output = subprocess.check_output(args, **kargv)
    output = output.decode('utf-8')
    return output


def run_cmd(*args: str, do_print: bool = True, **kargv) -> int:
    if (do_print, kargv.get("stdout")==subprocess.DEVNULL) == (True, False):
        print_cmd(*args)
    out = subprocess.call(args, **kargv)
    return out


def backtwo(arr) -> reversed:
    arr = zip(range(1, len(arr)), arr[1:], arr)
    return reversed(list(arr))


def mkvinfo(file, **kargv) -> Munch:
    arr = MyList()
    arr.extend("mkvmerge -F json --identify")
    arr.append(file)
    js = get_cmd(*arr, **kargv)
    js = json.loads(js)
    return DefaultMunch.fromDict(js)

def mediainfo(file):
    cwd = getcwd()
    dr = dirname(file)
    if dr:
        chdir(dr)
    out = get_cmd("mediainfo", basename(file), do_print=False)
    chdir(cwd)
    out = out.strip()
    arr = []
    for l in out.split("\n"):
        l = [i.strip() for i in l.split(" : ", 1)]
        arr.append(tuple(l))
    frt = max(len(i[0]) for i in arr)
    frt = "%-"+str(frt)+"s : %s"
    for i, l in enumerate(arr):
        if len(l)==1:
            arr[i]=l[0]
            continue
        arr[i] = frt % l
    out = "\n".join(arr)
    return out

class MkvLang:
    def __init__(self):
        def trim(s):
            s = s.strip()
            if len(s)==0:
                return None
            return s
        self.code = {}
        self.description = {}
        langs = get_cmd("mkvmerge", "--list-languages", do_print=False)
        for l in langs.strip().split("\n")[2:]:
            label, cod1, cod2 = map(trim, l.split(" |"))
            if cod1:
                self.code[cod1] = cod2
                self.description[cod1] = label
            if cod2:
                self.code[cod2] = cod1
                self.description[cod2] = label

MKVLANG = MkvLang()

class MyList(list):
    def extend(self, s, *args, **kwargs):
        """
        Si s es un str, lo formate con *args, **kwargs y le hace un split
        Si s es un list, formatea con *args, **kwargs todos sus elementos
        El resultado se pasa a super().extend
        """
        if isinstance(s, str):
            s = s.format(*args, **kwargs)
            s = s.split()
        elif args or kwargs:
            s = [str(i).format(*args, **kwargs) for i in s]
        super().extend(s)


class Sub:
    def __init__(self, file: str):
        self.file = file

    def _load(self):
        try:
            return pysubs2.load(self.file)
        except ValueError:
            typ = file.rsplit(".", 1)[-1].lower()
            with open(self.file, "r") as f:
                text = f.read()
            text = text.replace("Dialogue: Marked=0,", "Dialogue: 0,")
            return pysubs2.SSAFile.from_string(text, format=typ)

    def load(self, to_type: str = None) -> pysubs2.SSAFile:
        subs = self._load()
        subs.sort()
        if to_type and not self.file.endswith("." + to_type):
            strng = subs.to_string(to_type)
            if strng.strip():
                subs = pysubs2.SSAFile.from_string(strng, format=to_type)
            subs.sort()
        for i, s in reversed(list(enumerate(subs))):
            if re_nosub.search(s.text) or len(s.text.strip())==0:
                del subs[i]
        flag = len(subs) + 1
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

    @property
    def fonts(self) -> tuple:
        subs = self._load()
        fonts = set()
        for f in subs.styles.values():
            fonts.add(f.fontname)
            fonts.add(f.fontname.split()[0])
        fonts = sorted(fonts)
        return tuple(fonts)

    def save(self, out: str) -> str:
        if "." not in out:
            out = self.file.rsplit(".", 1)[0] + "." + out
        to_type = out.rsplit(".", 1)[-1]
        if out == self.file:
            out = out + "." + to_type
        subs = self.load(to_type=to_type)
        subs.save(out)
            
        if to_type == "srt":
            with open(out, "r") as f:
                text = f.read()
            n_text = re.sub(r"</(i|b)>([ \t]*)<\1>", r"\2", text)
            n_text = re.sub(r"<(i|b)>([ \t]*)</\1>", r"\2", text)
            if text != n_text:
                with open(out, "w") as f:
                    f.write(n_text)
        return out


class Track(DefaultMunch):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "track_name" not in self:
            self.track_name = None

    @property
    def lang(self) -> str:
        lg = [self.language_ietf, self.language]
        lg = [l for l in lg if l not in (None, "", "und")]
        if len(lg) == 0:
            return "und"
        lg = lg[0]
        if len(lg)==2 and MKVLANG.code.get(lg):
            lg = MKVLANG.code.get(lg)
        return lg

    @property
    def isUnd(self) -> bool:
        return self.lang in (None, "", "und")

    @property
    def lang_name(self) -> str:
        if self.lang in LANG_ES:
            return "Español"
        if self.lang in ("ja", "jpn"):
            return "Japonés"
        if self.lang in ("en", "eng"):
            return "Inglés"
        if self.lang in ("hi", "hin"):
            return "Hindi"
        if self.lang in ("ko", "kor"):
            return "Coreano"
        if self.lang in ("fr", "fre"):
            return "Francés"
        label = MKVLANG.description.get(self.lang)
        if label:
            return label
        return self.lang

    @property
    def isLatino(self) -> bool:
        if self.track_name is None or self.lang not in LANG_ES:
            return False
        if "latino" in self.track_name.lower():
            return True
        if self.track_name == "LRL":
            return True
        return False

    @property
    def file_extension(self) -> str:
        if self.codec == "SubStationAlpha":
            return "ssa"
        if self.codec == "SubRip/SRT":
            return "srt"
        if self.type == "subtitles" and "PGS" in self.codec:
            return "pgs"
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
        if self.codec in ("AAC",):
            return "aac"
        if self.codec == "VobSub":
            return "sub"
        raise Exception("Extensión no encontrada para: {codec}".format(**dict(self)))

    @property
    def new_name(self) -> str:
        if self.type == "video":
            lb = None
            if "H.264" in self.codec:
                lb = "H.264"
            if "H.265" in self.codec:
                lb = "H.265"
            if "HDMV" in self.codec:
                lb = "HDMV"
            if lb is None:
                return None
            if self.pixel_dimensions:
                lb = "{} ({})".format(lb, self.pixel_dimensions)
            if self.duration is not None and self.duration.minutes>59:
                lb = lb + " ({}m)".format(self.duration.minutes)
            return lb
        arr = [self.lang_name]
        if self.type == "subtitles" and self.forced_track:
            arr.append("forzados")
        if self.type == "audio" and self.track_name:
            m = [i for i in re_doblage.findall(self.track_name) if len(i)==4]
            if m:
                arr.append(m[0])
        arr.append("(" + self.file_extension + ")")
        if self.type == "subtitles" and self.lines:
            arr.append("({} línea{})".format(self.lines, "s" if self.lines>1 else ""))
        return " ".join(arr)

    def set_lang(self, lang):
        if len(lang)==3 and lang!=self.language_ietf:
            self.language_ietf = lang
            self.language = MKVLANG.code.get(lang)
            self.isNewLang = True
        if len(lang)==2 and lang!=self.language:
            self.language = lang
            self.language_ietf = MKVLANG.code.get(lang)
            self.isNewLang = True

    def to_dict(self) -> dict:
        d = dict(self)
        d['new_name'] = self.new_name
        d['file_extension'] = self.file_extension
        d['isLatino'] = self.isLatino
        d['lang'] = self.lang
        d['lang_name'] = self.lang_name
        d['track_name'] = self.track_name
        return d

    def get_changes(self, mini=False) -> DefaultMunch:
        chg = DefaultMunch(
            language=self.lang,
            track_name=self.new_name,
            default_track=int(self.get("default_track", 0)),
            forced_track=int(self.type == "subtitles" and bool(self.forced_track))
        )
        if mini:
            if not self.isNewLang:
                del chg["language"]
            if self._original:
                if chg.track_name == self._original.track_name:
                    del chg["track_name"]
                if chg.default_track == int(self._original.get("default_track", 0)):
                    del chg["default_track"]
                if chg.forced_track == int(self._original.get("forced_track", 0)):
                    del chg["forced_track"]
        return chg

class Duration:
    def __init__(self, nano):
        self.nano = nano

    @property
    def seconds(self):
        return self.nano / 1000000000

    @property
    def minutes(self):
        return round(self.seconds / 60)

    def __eq__(self, other):
        return self.nano == other.nano
        
class Mkv:
    def __init__(self, file: str, vo: str = None, und: str = None, only: list = None, source: int = 0, tracks_selected: list = None):
        self.file = file
        self._core = DefaultMunch()
        self.und = und
        self.vo = vo
        self.only = only
        self.source = source
        self.tracks_selected = tracks_selected

    def mkvextract(self, *args, model="tracks", **kwargs):
        if len(args) > 0:
            run_cmd("mkvextract", self.file, model, *args, **kwargs)

    def mkvpropedit(self, *args):
        if len(args) == 0:
            return
        run_cmd("mkvpropedit", self.file, *args)
        self._core = DefaultMunch()

    @property
    def extension(self) -> str:
        return self.file.rsplit(".")[-1].lower()

    @property
    def duration(self):
        d = self._core.info.container.properties.duration
        if d is None:
            #if self.extension in ("mp4", "avi"):
            arr = "ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1".split()
            arr.append(self.file)
            d = get_cmd(*arr, do_print=False)
            d = float(d) * 1000000000
        return Duration(d)

    @property
    def info(self) -> Munch:
        if self._core.info is None:
            self._core.info = mkvinfo(self.file)
        return self._core.info

    @property
    def attachments(self) -> tuple:
        arr = []
        for a in self.info.attachments:
            if a.id in self.ban.attachments:
                continue
            arr.append(a)
        return tuple(arr)

    @property
    def num_chapters(self):
        ch = 0
        for c in self.info.get("chapters", []):
            ch = c.get("num_entries", 0)
        return ch

    @property
    def chapters(self):
        if self.num_chapters == 0:
            return None
        if self._core.chapters is None:
            out = get_cmd("mkvextract", "chapters", self.file)
            out = out.strip()
            if len(out)==0:
                self._core.chapters = dict()
            else:
                self._core.chapters = xmltodict.parse(out.strip())
        return self._core.chapters
        

    @property
    def tracks(self) -> tuple:
        """
        :return: Lista de Track no baneadas
        """
        fl_name = self.file.lower()
        fl_name = set(n.strip() for n in re.split(r'(\W+)', fl_name) if n.strip())
        if self._core.tracks is None:
            arr = []
            for t in self.info.tracks:
                track = Track()
                track.update(t.properties.copy())
                track.id = t.id
                track.codec = t.codec
                track.type = t.type
                track.source = self.source
                track._original = t.properties.copy()
                if track.type == "video":
                    track.duration = self.duration
                    if self.vo is not None:
                        track.set_lang(self.vo)
                if track.lang in ("lat", "la"):
                    if track.track_name is None:
                        track.track_name = "Español latino"
                    elif "latino" not in track.track_name.lower():
                        track.track_name = track.track_name +" (latino)"
                    print("# {source}:{id} {track_name}: lat -> es".format(**dict(track)))
                    track.set_lang("spa")
                if track.isUnd and track.track_name is not None:
                    st_name = set(track.track_name.lower().split())
                    if st_name.intersection({"español", "castellano", "latino"}):
                        print("# {source}:{id} {track_name}: und -> es".format(**dict(track)))
                        track.set_lang("spa")
                    if st_name.intersection({"ingles", "english"}):
                        print("# {source}:{id} {track_name}: und -> en".format(**dict(track)))
                        track.set_lang("spa")
                arr.append(track)
            isAud = [t for t in arr if t.type == 'audio']
            if len(isAud)==1 and isAud[0].lang == 'und' and fl_name.intersection({"español", "castellano"}):
                track = isAud[0]
                print("# {source}:{id} {track_name}: und -> es".format(**dict(track)))
                track.set_lang("spa")
            for track in arr:
                if track.isUnd and self.und:
                    track.set_lang(self.und)
            isUnd = [t for t in arr if t.isUnd]
            if len(isUnd):
                print(isUnd)
                print("Es necesario pasar el parámetro --und")
                for s in isUnd:
                    print("# {source}:{id} {track_name} {codec}".format(**dict(s)))
                sys.exit()

            sub_text = [s for s in arr if s.type == "subtitles" and s.text_subtitles]
            att_font = [a for a in self._core.info.get("attachments", []) if a.get('content_type') in ("application/x-truetype-font", "application/vnd.ms-opentype")]
            fls = self.extract(*sub_text, *att_font, stdout=subprocess.DEVNULL)
            for f, s in zip(fls, sub_text + att_font):
                if isinstance(s, Track):
                    sb = Sub(to_utf8(f))
                    s.fonts = sb.fonts
                    lines = len(sb.load("srt"))
                    s.lines = lines
                else:
                    try:
                        out = get_cmd("otfinfo", "--info", f, do_print=False, stderr=subprocess.DEVNULL)
                    except subprocess.CalledProcessError:
                        continue
                    s.font = out.strip().split("\n")[0].split(":")[1].strip()

            subtitles = [s for s in arr if s.type == "subtitles" and s.lines != 0]
            if subtitles:
                sub_langs = {}
                for s in subtitles:
                    if s.lang not in sub_langs:
                        sub_langs[s.lang] = []
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
                            print("# {source}:{id} {track_name}: forced_track=1".format(**dict(track)))
                            s.forced_track = 1
                            forced_done = True
                    if forced_done is False:
                        subs = [s for s in subs if s.text_subtitles]
                        if len(subs)>0:
                            max_forced = self.duration.minutes
                            if len(subs)>1:
                                subs = sorted(subs, key=lambda x: x.lines)
                                max_forced = max(max_forced, subs[-1].lines)
                            if subs[0].lines < (max_forced / 2):
                                track = subs[0]
                                print("# {source}:{id} {track_name}: forced_track=1".format(**dict(track)))
                                track.forced_track = 1
            self._core.tracks = arr

        arr = []
        ban = set().union(self.ban.audio, self.ban.subtitles, self.ban.video)
        for t in self._core.tracks:
            if t.id in ban:
                continue
            arr.append(t)
        return tuple(arr)

    @property
    def ban(self) -> Munch:
        if self._core.ban is None:
            self._core.ban = Munch(
                audio=set(),
                subtitles=set(),
                video=set(),
                attachments=set()
            )
            if self.tracks_selected is True:
                return
            for s in self._core.tracks:
                if self.tracks_selected is not None:
                    srcid = "{}:{}".format(self.source, s.id)
                    if srcid not in self.tracks_selected:
                        print("# RM {} {track_name}".format(srcid, **dict(s)))
                        self._core.ban[s.type].add(s.id)
                    continue
                if s.type not in ('audio', 'subtitles'):
                    continue
                if s.type == 'subtitles' and s.lines == 0:
                    print("# RM {source}:{id}:{file_extension} {track_name} por estar vacio".format(**s.to_dict()))
                    self._core.ban.subtitles.add(s.id)
                    continue
                if self.only and s.file_extension not in self.only:
                    if s.type == 'subtitles':
                        self._core.ban.subtitles.add(s.id)
                        print("# RM {source}:{id}:{file_extension} {track_name} por extension".format(**s.to_dict()))
                    if s.type == 'audio':
                        self._core.ban.audio.add(s.id)
                        print("# RM {source}:{id}:{file_extension} {track_name} por extension".format(**s.to_dict()))
                    continue
                if s.lang and (s.isLatino or s.lang not in self.main_lang):
                    latino = " - latino" if s.isLatino else ""
                    if s.type == 'subtitles':
                        self._core.ban.subtitles.add(s.id)
                        print("# RM {source}:{id}:{file_extension} {track_name} por idioma ({lang}{latino})".format(latino=latino,
                                                                                                         **s.to_dict()))
                    if s.type == 'audio':
                        self._core.ban.audio.add(s.id)
                        print("# RM {source}:{id}:{file_extension} {track_name} por idioma ({lang}{latino})".format(latino=latino,
                                                                                                         **s.to_dict()))

            txt_sub = [c for c in self._core.tracks if c.type == "subtitles" and c.text_subtitles and c.file_extension != 'srt' and c.id not in self._core.ban.subtitles]

            fonts = set()
            for s in txt_sub:
                if s.fonts is not None:
                    fonts = fonts.union(s.fonts)

            for a in self.info.attachments:
                if len(txt_sub) == 0 or a.get('content_type') not in ("application/x-truetype-font", "application/vnd.ms-opentype"):
                    self.ban.attachments.add(a.id)
                    print("# RM {}:{id}:{content_type} {file_name} por tipo o falta de subtitulos != srt".format(self.source, **a))
                elif a.font is not None and a.font not in fonts:
                    self.ban.attachments.add(a.id)
                    print("# RM {}:{id}:{content_type} {file_name} {font} por no usarse en subtitulos".format(self.source, **a))
                    
        return self._core.ban

    @property
    def main_lang(self) -> tuple:
        langs = set(LANG_ES)
        for s in self.tracks:
            if s.type == 'video':
                if s.language_ietf:
                    langs.add(s.language_ietf)
                if s.language:
                    langs.add(s.language)
        return tuple(sorted(langs))

    def extract(self, *tracks, **kwargs) -> tuple:
        if len(tracks)==0:
            return []
        name = basename(self.file).rsplit(".", 1)[0]
        arrg = []
        outs = []
        lastModel = None
        for track in tracks:
            if isinstance(track, int):
                track = self.get_track(track)
            if isinstance(track, Track):
                model = "tracks"
                out = "{tmp}/{src}_{id}_{name}.{file_extension}".format(name=name, tmp=TMP, src=self.source, **track.to_dict())
            else:
                model = "attachments"
                out = "{tmp}/{src}_{id}_{name}_{file_name}".format(name=name, tmp=TMP, src=self.source, **dict(track))
            if lastModel != model:
                arrg.append(model)
                lastModel = model
            outs.append(out)
            arrg.append(str(track.id) + ":" + out)

        run_cmd("mkvextract", self.file, *arrg, **kwargs)
        return tuple(outs)

    def get_tracks(self, *typeids) -> tuple:
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
        return tuple(arr)

    def fix_tracks(self, mini=False):
        arr = MyList()
        title = get_title(self.file)
        if title != self.info.container.properties.title or not mini:
            arr.extend("--edit info --set")
            arr.append("title=" + title)

        defSub = None
        isAudEs = any(s for s in self.get_tracks('audio') if s.lang in LANG_ES)
        subEs = DefaultMunch()
        for s in self.get_tracks('subtitles'):
            if s.lang in LANG_ES:
                if s.forced_track and subEs.forc is None:
                    subEs.forc = s.number
                if not s.forced_track and subEs.full is None:
                    subEs.full = s.number
        if isAudEs:
            defSub = -1
            if subEs.forc is not None:
                defSub = subEs.forc
        elif subEs.full is not None:
            defSub = subEs.full

        doDefault = DefaultMunch()
        for s in self.tracks:
            if s.type in ("video", "audio"):
                if doDefault[s.type] is None:
                    doDefault[s.type] = s.number
                s.default_track = int(s.number == doDefault[s.type])
            if s.type == "subtitles" and defSub is not None:
                s.default_track = int(s.number == defSub)

        for s in self.tracks:
            arr_track = MyList()
            chg = s.get_changes(mini=mini)
            if chg.language is not None:
                arr_track.extend("--set language={}", chg.language)
            if chg.default_track is not None:
                arr_track.extend("--set flag-default={}", chg.default_track)
            if chg.track_name is not None:
                arr_track.extend(["--set", "name=" + chg.track_name])
            if chg.forced_track is not None:
                arr_track.extend("--set flag-forced={}", chg.forced_track)
            if arr_track:
                arr.extend("--edit track:{}", s.number)
                arr.extend(arr_track)

        self.mkvpropedit(*arr)

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
            track = full
        if track is not None:
            name = self.file.rsplit(".", 1)[0]
            out = "{0}:{1}.{2}".format(track.id, name, track.file_extension)
            print("# Para extraer el subtítulo principal haz:")
            print_cmd("mkvextract", "tracks", self.file, out)


class MkvMerge:
    def __init__(self, vo: str = None, und: str = None, do_srt: bool = False, do_ac3: bool = False, only: list = None):
        self.vo = vo
        self.und = und
        self.do_srt = do_srt
        self.do_ac3 = do_ac3
        self.only = only

    def mkvmerge(self, output: str, *args) -> Mkv:
        if len(args) == 0 or len(args) == 1 and args[0] == self.file:
            return
        run_cmd("mkvmerge", "-o", output, *args)
        mkv = Mkv(output)
        mkv.fix_tracks(mini=True)
        return mkv

    def get_tracks(self, typ: str, src: list) -> tuple:
        arr = []
        for s in src:
            if isinstance(s, Mkv):
                arr.extend(s.get_tracks(typ))
            elif s.type == typ:
                arr.append(s)
        return tuple(arr)

    def get_extract(self, src: list, track: list) -> tuple:
        arr = []
        sources = sorted(set(s.source for s in track))
        for s in sources:
            t = sorted((t for t in track if t.source == s), key=lambda x: x.id)
            s = src[s]
            if isinstance(s, Mkv):
                fls = s.extract(*t)
                arr.extend(list(zip(t, fls)))
            else:
                arr.append((s, s.source_file))
        return tuple(arr)

    def make_order(self, src: list, main_order: list = None) -> str:
        """
        1. pista de video
        2. pistas de audio:
            1. es ac3
            2. vo ac3
            3. ** ac3
            4. es ***
            5. vo ***
            6. ** ***
        3. pistas de subtítulo:
            1. es completos
            2. es forzados
            3. vo completos
            4. vo forzados
            5. ** completos
            6. ** forzados
        """
        main_lang = set(LANG_ES)
        for s in self.get_tracks('video', src):
            if s.language_ietf:
                main_lang.add(s.language_ietf)
            if s.language:
                main_lang.add(s.language)
        main_lang = tuple(sorted(main_lang))

        indx_s = lambda x, *arr: arr.index(x) if x in arr else len(arr)
        sort_s = lambda x: (x.source, -x.get('lines', 0), x.number)
        orde = sorted(self.get_tracks('video', src), key=sort_s)
        aux = Munch(
            es=[],
            mn=[],
        )
        for s in self.get_tracks('audio', src):
            if s.lang in LANG_ES:
                aux.es.append(s)
                continue
            if s.lang in main_lang:
                aux.mn.append(s)
                continue
            if s.lang not in aux:
                aux[s.lang]=[]
            aux[s.lang].append(s)
        for k in aux.keys():
            aux[k]=sorted(aux[k], key=lambda s: (indx_s(s.file_extension, "ac3"), s.source, s.number))
        for ss in zip_longest(aux.es, aux.mn):
            for s in ss:
                if s is not None:
                    orde.append(s)

        hasAudEs = bool(len(aux.es))

        sort_s = lambda x: (x.source, -x.get('lines', 0), x.number)
        aux = Munch(
            es_ful=[],
            es_for=[],
            mn_ful=[],
            mn_for=[],
            ot_ful=[],
            ot_for=[],
        )
        for s in self.get_tracks('subtitles', src):
            if s.forced_track:
                if s.lang in LANG_ES:
                    aux.es_for.append(s)
                    continue
                if s.lang in main_lang:
                    aux.mn_for.append(s)
                    continue
                aux.ot_for.append(s)
                continue
            if s.lang in LANG_ES:
                aux.es_ful.append(s)
                continue
            if s.lang in main_lang:
                aux.mn_ful.append(s)
                continue
            aux.ot_for.append(s)

        for a in aux.values():
            orde.extend(sorted(a, key=sort_s))

        if main_order is not None:
            orde = sorted(orde, key=lambda s: main_order.index("{source}:{id}".format(**dict(s))))

        defSub = None
        if hasAudEs and aux.es_for:
            defSub = aux.es_for[0]
        elif not(hasAudEs) and aux.es_ful:
            defSub = aux.es_ful[0]

        defTrack = set()
        newordr = []
        for o, s in enumerate(orde):
            if s.type in ("video", "audio"):
                s.default_track = int(s.type not in defTrack)
                defTrack.add(s.type)
            elif s.type == "subtitles":
                s.default_track = int(s == defSub)
            newordr.append("{}:{}".format(s.source, s.id))

        return newordr

    def build_track(self, file: str, source: int) -> Track:
        nf = mkvinfo(file)
        t = nf.tracks[0]
        
        if t.get('type') == "subtitles":
            f = to_utf8(file)
            if f not in (None, file):
                return self.build_track(f, source)
            
        track = Track()
        track.update(t.properties.copy())
        track.id = t.id
        track.codec = t.codec
        track.type = t.type
        track.source_file = file
        track.source = source
        if track.isUnd:
            lw_name = basename(file).lower()
            st_name = set(re.split(r"[\.]+", lw_name))
            if re.search(r"\b(español|castellano|spanish|)\b|\[esp\]", lw_name) or st_name.intersection({"es", }):
                track.set_lang("spa")
            if re.search(r"\b(ingles|english)\b", lw_name) or st_name.intersection({"en", }):
                track.set_lang("eng")
            if re.search(r"\b(japon[ée]s|japanese)\b", lw_name) or st_name.intersection({"ja", }):
                track.set_lang("jpn")
            if track.isUnd:
                track.set_lang(self.und or "und")
            if re.search(r"\b(forzados?)\b", lw_name) or st_name.intersection({"forzados", "forzado"}):
                track.forced_track = 1
        if track.type == 'subtitles':
            track.lines = len(Sub(file).load("srt"))
        if len(nf.get("chapters", [])) == 1 and nf.chapters[0].num_entries == 1:
            track.rm_chapters = True
        if track.track_name is None:
            track.track_name = basename(file)
            track.fake_name = True
        return track

    def merge(self, output: str, *files: Track, tracks_selected: list = None) -> Mkv:
        src = []
        for i, f in enumerate(files):
            ext = f.rsplit(".", 1)[-1].lower()
            if ext in ("mkv", "mp4", "avi"):
                mkv = Mkv(f, source=i, und=self.und, only=self.only, vo=self.vo, tracks_selected=tracks_selected)
                src.append(mkv)
            else:
                track = self.build_track(f, source=i)
                src.append(track)

        videos = self.get_tracks('video', src)
        if len(videos)>1:
            pxd = {}
            for v in videos:
                h, w = map(int, v.pixel_dimensions.split("x"))
                if w not in pxd:
                    pxd[w] = {}
                if h not in pxd[w]:
                    pxd[w][h] = []
                pxd[w][h].append(v)
            mx_w = max(pxd.keys())
            mn_h = min(pxd[mx_w].keys())
            main_video = pxd[mx_w][mn_h][0]
            print("# OK {source}:{id} {pixel_dimensions}".format(**main_video))
            for i, s in enumerate(src):
                if i != main_video.source and isinstance(s, Mkv):
                    for v in s.get_tracks('video'):
                        print("# KO {source}:{id} {pixel_dimensions}".format(**v))
                        s.ban.video.add(v.id)

        subtitles = self.get_tracks('subtitles', src)
        audio = self.get_tracks('audio', src)

        if len(subtitles) == 1 and subtitles[0].isUnd:
            subtitles[0].set_lang("spa")

        sub_langs = {}
        for s in subtitles:
            if s.lang not in sub_langs:
                sub_langs[s.lang] = []
            sub_langs[s.lang].append(s)

        for subs in sub_langs.values():
            if any(s.forced_track for s in subs):
                continue
            subs = [s for s in subs if s.text_subtitles]
            if len(subs) > 1:
                subs = sorted(subs, key=lambda x: x.lines)
                if subs[0].lines < (subs[-1].lines / 2):
                    track = subs[0]
                    print("# {source}:{id} {track_name}: forced_track=1".format(**dict(track)))
                    track.forced_track = 1

        no_text = [s for s in subtitles if not s.text_subtitles]
        si_text = set((s.lang, s.forced_track) for s in subtitles if s.text_subtitles)
        for s in no_text:
            if (s.lang, s.forced_track) in si_text:
                mkv = src[s.source]
                if isinstance(mkv, Mkv):
                    print("# RM {source}:{id}:{file_extension} {new_name} por existir alternativa en texto".format(**s.to_dict()))
                    mkv.ban[s.type].add(s.id)

        subtitles = self.get_tracks('subtitles', src)
        done = {}
        for s in subtitles + audio:
            k = (s.lang, s.file_extension, s.forced_track, s.type)
            if k in done and done[k]!=s.source:
                mkv = src[s.source]
                if isinstance(mkv, Mkv):
                    print("# RM {source}:{id}:{file_extension} {new_name} por duplicado".format(**s.to_dict()))
                    mkv.ban[s.type].add(s.id)
            done[k]=s.source

        subtitles = self.get_tracks('subtitles', src)
        audio = self.get_tracks('audio', src)

        si_srt = []
        no_srt = []
        for s in subtitles:
            if s.codec == "SubRip/SRT":
                si_srt.append(s)
            else:
                no_srt.append(s)

        si_ac3 = set()
        for s in audio:
            if s.file_extension == "ac3":
                if s.language_ietf:
                    si_ac3.add(s.language_ietf)
                if s.language:
                    si_ac3.add(s.language)

        cv_aud = []
        for s in audio:
            if s.language_ietf not in si_ac3 and s.language not in si_ac3:
                cv_aud.append(s)

        if self.do_ac3 and len(cv_aud) > 0:
            for s, ori in self.get_extract(src, *cv_aud):
                out = ori.rsplit(".", 1)[0] + ".ac3"
                run_cmd("ffmpeg", "-hide_banner", "-loglevel", "error", "-i", ori, "-acodec", "ac3", out)
                new_s = Track(s)
                new_s.id = 0
                new_s.source = len(src)
                new_s.source_file = out
                new_s.codec = "AC-3"
                src.append(new_s)

        if self.do_srt and len(si_srt) == 0 and len(no_srt) > 0:
            for s, ori in self.get_extract(src, *no_srt):
                out = Sub(ori).save("srt")
                new_s = Track(s)
                new_s.id = 0
                new_s.source = len(src)
                new_s.source_file = out
                new_s.codec = "SubRip/SRT"
                src.append(new_s)

        newordr = self.make_order(src, main_order=tracks_selected)
        
        
        arr = MyList()
        arr.extend(["--title", get_title(output)])
        for s in src:
            if isinstance(s, Mkv):
                mkv = s
                if mkv.ban.video:
                    nop = ",".join(map(str, sorted(mkv.ban.video)))
                    arr.extend("-d !{}", nop)
                if mkv.ban.subtitles:
                    nop = ",".join(map(str, sorted(mkv.ban.subtitles)))
                    arr.extend("-s !{}", nop)
                if mkv.ban.audio:
                    nop = ",".join(map(str, sorted(mkv.ban.audio)))
                    arr.extend("-a !{}", nop)
                if len(mkv.ban.attachments) == 0:
                    pass
                if len(mkv.attachments) == 0:
                    arr.append("--no-attachments")
                elif len(mkv.attachments) < len(mkv.info.attachments):
                    sip = ",".join(map(str, sorted(a.id for a in mkv.attachments)))
                    arr.extend("-m {}", sip)
                if mkv.num_chapters == 1:
                    arr.extend("--no-chapters")
                for t in sorted(mkv.tracks, key=lambda x: newordr.index("{source}:{id}".format(**dict(x)))):
                    chg = t.get_changes()
                    arr.extend("--language {}:{}", t.id, chg.language)
                    arr.extend("--default-track {}:{}", t.id, chg.default_track)
                    arr.extend("--forced-track {}:{}", t.id, chg.forced_track)
                    arr.extend(["--track-name", "{}:{}".format(t.id, chg.track_name)])
                arr.append(mkv.file)
            else:
                chg = s.get_changes()
                arr.extend("--language {}:{}", s.id, chg.language)
                arr.extend("--default-track {}:{}", s.id, chg.default_track)
                arr.extend("--forced-track {}:{}", s.id, chg.forced_track)
                arr.extend(["--track-name", "{}:{}".format(s.id, chg.track_name)])
                if s.rm_chapters:
                    arr.extend("--no-chapters")
                if s.type == 'subtitles':
                    arr.extend("--sub-charset {}:{}", s.id, get_encoding_type(s.source_file))
                arr.append(s.source_file)
        
        arr.extend("--track-order " + ",".join(newordr))
        mkv = self.mkvmerge(output, *arr)

        print("#", mkv.info.container.properties.title)
        for t in mkv.tracks:
            print ("# {id}:{language} {track_name}".format(**dict(t)))
        mkv.sub_extract()
        return mkv


if __name__ == "__main__":
    if len(sys.argv) == 2:
        fln = sys.argv[1]
        ext = fln.rsplit(".", 1)[-1].lower()
        if isfile(fln) and ext in ("srt", "ssa", "ass"):
            out = Sub(to_utf8(fln)).save("srt")
            print("OUT:", out)
            sys.exit()
    if len(sys.argv) > 2 and sys.argv[1]=="info":
        print("[spoiler=mediainfo][code]", end="")
        fls = sys.argv[2:]
        for i, f in enumerate(fls):
            out = mediainfo(f)
            if len(fls)>1:
                print("$", "mediainfo '"+basename(f)+"'")
            print(out, end="" if i==len(fls)-1 else "\n\n")
        print("[/code][/spoiler]")
        sys.exit()

    langs = sorted(k for k in MKVLANG.code.keys() if len(k) == 2)
    parser = argparse.ArgumentParser("Remezcla mkv")
    parser.add_argument('--und', help='Idioma para pistas und (mkvmerge --list-languages)', choices=langs)
    parser.add_argument('--vo', help='Idioma de la versión original (mkvmerge --list-languages)', choices=langs)
    parser.add_argument('--do-srt', action='store_true', help='Genera subtitulos srt si no los hay')
    parser.add_argument('--do-ac3', action='store_true', help='Genera audio ac3 si no lo hay')
    parser.add_argument('--only', nargs="*", help='Permitir solo ciertos tipos de audio y subtitulos (ac3, srt, etc)')
    parser.add_argument('--tracks', nargs="*", help='tracks a preservar en formato source:id')
    parser.add_argument('--out', type=str, help='Fichero salida para mkvmerge')
    parser.add_argument('files', nargs="+", help='Ficheros a mezclar')
    pargs = parser.parse_args()

    if pargs.out in pargs.files:
        sys.exit("El fichero de entrada y salida no pueden ser el mismo")
    for file in pargs.files:
        if not isfile(file):
            sys.exit("No existe: " + file)

    print("$", "mkdir", TMP)
    mrg = MkvMerge(und=pargs.und, do_srt=pargs.do_srt, do_ac3=pargs.do_ac3, only=pargs.only, vo=pargs.vo)
    mrg.merge(pargs.out, *pargs.files, tracks_selected=pargs.tracks)
