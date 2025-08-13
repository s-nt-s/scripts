import zlib
import base64
import subprocess
from os import getcwd, chdir
from os.path import basename, dirname
import requests
import sys

def get_cmd(*args: str, **kwargs) -> str:
    output = subprocess.check_output(args, **kwargs)
    output = output.decode(sys.stdout.encoding)
    return output

class zb64:
   def __init(self):
      pass

   def unzip(self, a):
      a = a.encode()
      a = base64.b64decode(a)
      a = zlib.decompress(a)
      a = a.decode()
      return a

   def zip(sefl, a):
      a = a.encode()
      a = zlib.compress(a)
      a = base64.b64encode(a)
      a = a.decode()
      return a

class Mediainfo:
   def __init__(self, file):
      self.file = file
      current = getcwd()
      fdrname = dirname(self.file)
      if fdrname:
         chdir(fdrname)
      self._s_xml = get_cmd("mediainfo", "--Output=XML", self.name)
      self._s_txt = get_cmd("mediainfo", self.name)
      chdir(current)
      self.url = None

   @property
   def name(self):
      return basename(self.file)

   @property
   def txt(self):
      out = self._s_txt.strip()
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

   def publish(self):
      if self.url is None:
         data = {
            "xml": zb64().zip(self._s_xml),
            "expiration": "-1",
            "title": self.name,
            "visibility": "0",
            "anonymize": "0",
         }
         r = requests.put("https://mediaarea.net/api/v1/MediaBin", data=data)
         self.url = r.json()['url']
      return self.url

if __name__ == "__main__":
   mi = Mediainfo(sys.argv[1])
   print(mi.txt)
   print("")
   print(mi.publish())
