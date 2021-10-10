#!/usr/bin/python3
import subprocess
import json
import argparse
import tempfile
import sys
from munch import Munch, DefaultMunch
from functools import lru_cache
from os.path import isfile, basename, dirname, realpath
import re
import pysubs2

re_sp = re.compile(r"\s+")
TMP = tempfile.mkdtemp()
re_nosub = re.compile(r"www\.newpct\.com")

LANG_ES = ("es", "spa", "es-ES")


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
            elif args[index - 2] == "-o":
                a = "\\\n  " + a
            elif isfile(args[index - 1]):
                a = "\\\n  " + a
        arr.append(a)
    print("$", *arr)


def get_cmd(*args: str, do_print: bool = True) -> str:
    if do_print:
        print_cmd(*args)
    output = subprocess.check_output(args)
    output = output.decode('utf-8')
    return output


def run_cmd(*args: str, do_print: bool = True, silent: bool = False) -> int:
    if (do_print, silent) == (True, False):
        print_cmd(*args)
    stdout = None
    if silent:
        stdout = subprocess.DEVNULL
    out = subprocess.call(args, stdout=stdout)
    return out


def backtwo(arr) -> reversed:
    arr = zip(range(1, len(arr)), arr[1:], arr)
    return reversed(list(arr))


def mkvinfo(file) -> Munch:
    arr = MyList()
    arr.extend("mkvmerge -F json --identify")
    arr.append(file)
    js = get_cmd(*arr)
    js = json.loads(js)
    return DefaultMunch.fromDict(js)

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

    def load(self, to_type: str = None) -> pysubs2.SSAFile:
        subs = pysubs2.load(self.file)
        subs.sort()
        if to_type and not self.file.endswith("." + to_type):
            subs = pysubs2.SSAFile.from_string(subs.to_string(to_type))
            subs.sort()
        for i, s in reversed(list(enumerate(subs))):
            if re_nosub.search(s.text):
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

    def save(self, out: str) -> str:
        if "." not in out:
            out = self.file.rsplit(".", 1)[0] + "." + out
        to_type = out.rsplit(".", 1)[-1]
        if out == self.file:
            out = out + "." + to_type
        subs = self.load(to_type=to_type)
        subs.save(out)
        return out


class Track(DefaultMunch):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def lang(self) -> str:
        lg = [self.language_ietf, self.language]
        lg = [l for l in lg if l not in (None, "", "und")]
        if len(lg) == 0:
            return "und"
        return lg[0]

    @property
    def isUnd(self) -> bool:
        return self.lang in (None, "", "und")

    @property
    def lang_name(self) -> str:
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
        raise Exception("Extensión no encontrada para: {codec}".format(**dict(self)))

    @property
    def new_name(self) -> str:
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
        arr = [self.lang_name]
        if self.forced_track and self.type == "subtitles":
            arr.append("forzados")
        arr.append("(" + self.file_extension + ")")
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


class Mkv:
    def __init__(self, file: str, vo: str = None, und: str = None, only: list = None, source: int = 0):
        self.file = file
        self._core = DefaultMunch()
        self.und = und
        self.vo = vo
        self.only = only
        self.source = source

    def mkvextract(self, *args, **kwargs):
        if len(args) > 0:
            run_cmd("mkvextract", "tracks", self.file, *args, **kwargs)

    def mkvpropedit(self, *args):
        if len(args) == 0:
            return
        run_cmd("mkvpropedit", self.file, *args)
        self._core = DefaultMunch()

    @property
    def info(self) -> Munch:
        if self._core.info is None:
            self._core.info = mkvinfo(self.file)
        return self._core.info

    @property
    def attachments(self) -> list:
        arr = []
        for a in self.info.attachments:
            if a.id in self.ban.attachments:
                continue
            arr.append(a)
        return arr

    @property
    def tracks(self) -> list:
        """
        :return: Lista de Track no baneadas
        """
        if self._core.tracks is None:
            arr = []
            for t in self.info.tracks:
                track = Track()
                track.update(t.properties.copy())
                track.id = t.id
                track.codec = t.codec
                track.type = t.type
                track.source = self.source
                if self.vo is not None and track.type == "video":
                    track.set_lang(self.vo)
                if track.lang == 'und' and track.track_name is not None:
                    st_name = set(track.track_name.lower().split())
                    if st_name.intersection({"español", "castellano"}):
                        print("# track {id} {track_name}: und -> es".format(**dict(track)))
                        track.set_lang("spa")
                    if st_name.intersection({"ingles", "english"}):
                        print("# track {id} {track_name}: und -> en".format(**dict(track)))
                        track.set_lang("spa")
                if track.lang == 'und' and self.und:
                    track.set_lang(self.und)
                arr.append(track)
            isUnd = [t for t in arr if t.lang == 'und']
            if len(isUnd):
                print("Es necesario pasar el parámetro --und")
                for s in isUnd:
                    print("# track {id} {track_name} {codec}".format(**dict(s)))
                sys.exit()

            subtitles = [s for s in arr if s.type == "subtitles"]
            if subtitles:
                fls = self.extract(*subtitles, silent=True)
                for f, s in zip(fls, subtitles):
                    lines = len(Sub(f).load("srt"))
                    s.lines = lines

                sub_langs = {}
                for s in subtitles:
                    if s.lines == 0:
                        continue
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
                            print("# track {id} {track_name}: forced_track=1".format(**dict(track)))
                            s.forced_track = 1
                            forced_done = True
                    if forced_done is False and len(subs) > 1:
                        subs = sorted(subs, key=lambda x: x.lines)
                        if subs[0].lines < (subs[-1].lines / 2):
                            track = subs[0]
                            print("# track {id} {track_name}: forced_track=1".format(**dict(track)))
                            track.forced_track = 1
            self._core.tracks = arr

        arr = []
        ban = set().union(self.ban.audio, self.ban.subtitles, self.ban.video)
        for t in self._core.tracks:
            if t.id in ban:
                continue
            arr.append(t)
        return arr

    @property
    def ban(self) -> Munch:
        if self._core.ban is None:
            self._core.ban = Munch(
                audio=set(),
                subtitles=set(),
                video=set(),
                attachments=set()
            )
            for s in self._core.tracks:
                if s.type not in ('audio', 'subtitles'):
                    continue
                if s.type == 'subtitles' and s.lines == 0:
                    print("# RM {file_extension} {id} {track_name} por estar vacio".format(**s.to_dict()))
                    self._core.ban.subtitles.add(s.id)
                    continue
                if self.only and s.file_extension not in self.only:
                    if s.type == 'subtitles':
                        self._core.ban.subtitles.add(s.id)
                        print("# RM {file_extension} {id} {track_name} por extension".format(**s.to_dict()))
                    if s.type == 'audio':
                        self._core.ban.audio.add(s.id)
                        print("# RM {file_extension} {id} {track_name} por extension".format(**s.to_dict()))
                    continue
                if s.lang and (s.isLatino or s.lang not in self.main_lang):
                    latino = " - latino" if s.isLatino else ""
                    if s.type == 'subtitles':
                        self._core.ban.subtitles.add(s.id)
                        print(
                            "# RM {file_extension} {id} {track_name} por idioma ({lang}{latino})".format(latino=latino,
                                                                                                         **s.to_dict()))
                    if s.type == 'audio':
                        self._core.ban.audio.add(s.id)
                        print(
                            "# RM {file_extension} {id} {track_name} por idioma ({lang}{latino})".format(latino=latino,
                                                                                                         **s.to_dict()))

            c_sub = len([c for c in self.get_tracks('subtitles') if
                         c.file_extension != 'srt' and c.id not in self._core.ban.subtitles])
            for a in self.info.attachments:
                if c_sub == 0 or a.get('content_type') not in (
                        "application/x-truetype-font", "application/vnd.ms-opentype"):
                    self.ban.attachments.add(a.id)
                    print("# RM {content_type} {id} por tipo o falta de subtitulos != srt".format(**a))

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

    def extract(self, *tracks, **kwargs) -> list:
        arrg = []
        outs = []
        for track in tracks:
            if isinstance(track, int):
                track = self.get_track(track)
            if track.file_extension is None:
                raise Exception(
                    "La pista {id} con tipo {type} y formato {codec} no tiene extension".format(**track))
            out = "{tmp}/{source}_{id}.{file_extension}".format(tmp=TMP, **track.to_dict())
            outs.append(out)
            arrg.append(str(track.id) + ":" + out)
        self.mkvextract(*arrg, **kwargs)
        return outs

    def get_tracks(self, *typeids) -> list:
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

    def fix_tracks(self):
        arr = MyList()
        arr.extend("--edit info --set")
        arr.append("title=" + get_title(self.file))

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
            arr.extend("--edit track:{}", s.number)
            if s.new_name:
                arr.extend(["--set", "name=" + s.new_name])
            arr.extend("--set language={}", s.lang)
            if s.type in ("video", "audio"):
                if doDefault[s.type] is None:
                    doDefault[s.type] = s.number
                arr.extend("--set flag-default={}", str(int(s.number == doDefault[s.type])))
            if s.type == "subtitles":
                if defSub is not None:
                    arr.extend("--set flag-default={}", str(int(s.number == defSub)))
                arr.extend("--set flag-forced={}", str(int(s.forced_track)))

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
        mkv.fix_tracks()
        return mkv

    def get_tracks(self, typ: str, src: list) -> list:
        arr = []
        for s in src:
            if isinstance(s, Mkv):
                arr.extend(s.get_tracks(typ))
            elif s.type == typ:
                arr.append(s)
        return arr

    def get_extract(self, src: list, track: list) -> list:
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
        return arr

    def get_order(self, src: list) -> str:
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

        sort_s = lambda x: (x.source, x.number)
        orde = sorted(self.get_tracks('video', src), key=sort_s)
        aux = Munch(
            es_ac3=[],
            mn_ac3=[],
            ot_ac3=[],
            es_otr=[],
            mn_otr=[],
            ot_otr=[],
        )
        for s in self.get_tracks('audio', src):
            if s.file_extension == "ac3":
                if s.lang in LANG_ES:
                    aux.es_ac3.append(s)
                    continue
                if s.lang in main_lang:
                    aux.mn_ac3.append(s)
                    continue
                aux.ot_ac3.append(s)
                continue
            if s.lang in LANG_ES:
                aux.es_otr.append(s)
                continue
            if s.lang in main_lang:
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

        reorder = False
        newordr = []
        for o, s in enumerate(orde):
            newordr.append("{}:{}".format(s.source, s.id))
            if s.number != (o + 1) or s.source != 0:
                reorder = True

        # if reorder is False:
        #    return None

        return ",".join(newordr)

    def build_track(self, file: str, source: int) -> Track:
        nf = mkvinfo(file)
        t = nf.tracks[0]
        track = Track()
        track.update(t.properties.copy())
        track.id = t.id
        track.codec = t.codec
        track.type = t.type
        track.source_file = file
        track.source = source
        if track.isUnd:
            st_name = set(re.split(r"[\s\.]+", basename(file).lower()))
            if st_name.intersection({"español", "castellano", "es"}):
                track.set_lang("spa")
            if st_name.intersection({"ingles", "english", "en"}):
                track.set_lang("eng")
            if st_name.intersection({"japones", "japanese", "ja"}):
                track.set_lang("jpn")
            if track.isUnd:
                track.set_lang("und")
        if len(nf.get("chapters", [])) == 1 and nf.chapters[0].num_entries == 1:
            track.rm_chapters = True
        return track

    def merge(self, output: str, *files: Track) -> Mkv:
        src = []
        for i, f in enumerate(files):
            ext = f.rsplit(".", 1)[-1].lower()
            if ext in ("mkv", "mp4"):
                mkv = Mkv(f, source=i, und=self.und, only=self.only, vo=self.vo)
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
            print("# OK source={source} track={id} {pixel_dimensions}".format(**main_video))
            for i, s in enumerate(src):
                if i != main_video.source and isinstance(s, Mkv):
                    for v in s.get_tracks('video'):
                        print("# KO source={source} track={id} {pixel_dimensions}".format(**v))
                        s.ban.video.add(v.id)

        subtitles = self.get_tracks('subtitles', src)
        audio = self.get_tracks('audio', src)

        if len(subtitles) == 1 and subtitles[0].isUnd:
            subtitles[0].set_lang("spa")

        done = set()
        for s in subtitles + audio:
            k = (s.lang, s.file_extension, s.forced_track, s.type)
            if k in done:
                mkv = src[s.source]
                if isinstance(mkv, Mkv):
                    print("# DP source={source} track={id} {new_name}".format(**s.to_dict()))
                    mkv.ban[s.type].add(s.id)
            done.add(k)

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

        arr = MyList()
        for s in src:
            if isinstance(s, Mkv):
                mkv = s
                for t in mkv.tracks:
                    if t.isNewLang:
                        arr.extend("--language {}:{}", t.id, t.lang)
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
                    sip = ",".join(map(str, sorted(a.id for a in self.attachments)))
                    arr.extend("-m {}", sip)
                arr.append(mkv.file)
            else:
                if s.lang:
                    arr.extend("--language 0:" + s.lang)
                if s.default_track:
                    arr.extend("--default-track 0:yes")
                if s.forced_track:
                    arr.extend("--forced-track 0:yes")
                if s.track_name:
                    arr.extend(["--track-name", "0:{track_name}"], **s)
                if s.rm_chapters:
                    arr.extend("--no-chapters")
                if s.type == 'subtitles':
                    arr.extend("--sub-charset 0:UTF-8")
                arr.append(s.source_file)

        newordr = self.get_order(src)
        if newordr:
            arr.extend("--track-order " + newordr)
        mkv = self.mkvmerge(output, *arr)
        mkv.sub_extract()
        return mkv


if __name__ == "__main__":
    if len(sys.argv) == 2:
        fln = sys.argv[1]
        ext = fln.rsplit(".", 1)[-1].lower()
        if isfile(fln) and ext in ("srt", "ssa"):
            out = Sub(fln).save("srt")
            print("OUT:", out)
            sys.exit()

    langs = sorted(k for k in MKVLANG.code.keys() if len(k) == 2)
    parser = argparse.ArgumentParser("Convierte los subtitulos de a srt")
    parser.add_argument('--und', help='Idioma para pistas und (mkvmerge --list-languages)', choices=langs)
    parser.add_argument('--vo', help='Idioma de la versión original (mkvmerge --list-languages)', choices=langs)
    parser.add_argument('--track', type=int, help='Extraer una pista')
    parser.add_argument('--do-srt', action='store_true', help='Genera subtitulos srt si no los hay')
    parser.add_argument('--do-ac3', action='store_true', help='Genera audio ac3 si no lo hay')
    parser.add_argument('--only', nargs="*", help='Permitir solo ciertos tipos de audio y subtitulos (ac3, srt, etc)')
    parser.add_argument('--out', type=str, help='Fichero salida para mkvmerge')
    parser.add_argument('files', nargs="+", help='Ficheros a mezclar')
    pargs = parser.parse_args()

    if pargs.out in pargs.files:
        sys.exit("El fichero de entrada y salida no pueden ser el mismo")
    for file in pargs.files:
        if not isfile(file):
            sys.exit("No existe: " + file)

    mrg = MkvMerge(und=pargs.und, do_srt=pargs.do_srt, do_ac3=pargs.do_ac3, only=pargs.only, vo=pargs.vo)
    mrg.merge(pargs.out, *pargs.files)
