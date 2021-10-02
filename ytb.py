#!/usr/bin/env python3

import youtube_dl
import argparse
import json

parser = argparse.ArgumentParser(description='youtube-dl wrapper')
parser.add_argument('--name', help="Nombre del fichero (sin extensión)", default='%(title)s')
parser.add_argument('--hd', action="store_true", help="Bajar máxima resolución disponible")
#parser.add_argument('--sub', action="store_true", help="Bajar subtítulos")
parser.add_argument('url', help="Url")

arg = parser.parse_args()

def pp(key, **kargv):
    kargv["key"]=key
    return kargv

def_opt = {
    'outtmpl': arg.name+'.%(ext)s',
    #'format': 'mp4+mp4', #'bestvideo+bestaudio',
    'noplaylist' : True,
    'restrictfilenames': True,
    'writesubtitles': True,
    'writeautomaticsub': True,
    #'allsubtitles':True,
    'subtitleslangs':['es', 'en'],
    'embedsubtitles': True,
    'merge_output_format': 'mkv',
    'postprocessors':[
        pp('FFmpegSubtitlesConvertor', format='srt'),
        pp('FFmpegEmbedSubtitle'),
    ]
}

def save(obj, target):
    with open(target, "w") as f:
        json.dump(obj, f, indent=2)

def dwn(opt):
    isFormat = ('format' in opt)
    with youtube_dl.YoutubeDL(opt) as ydl:
        result = ydl.extract_info(
            arg.url,
            download=isFormat
        )
    if not isFormat:
        save(result, "/tmp/"+result["id"]+".json")
        if "es" in result["subtitles"]:
            opt['subtitleslangs']=['es', 'en']
        else:
            opt['subtitleslangs']=['en', 'es']
        video = None
        audio = None
        for f in result["formats"]:
            if f["ext"] not in ("mp4", "m4a"):
                continue
            height = f.get("height")
            abr = f.get("abr")
            if height and (height<721 or arg.hd) and(video is None or height>=video["height"]):
                video=f
            if abr and(audio is None or abr>=audio["abr"]):
                audio=f
        opt['format']='{}+{}'.format(video['format_id'], audio['format_id'])
        dwn(opt)
        #print(json.dumps(result, indent=2))

dwn(def_opt)
