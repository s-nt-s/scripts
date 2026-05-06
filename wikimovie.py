#!/usr/bin/env python3
import requests
import argparse
import sys

from wikibaseintegrator.datatypes import ExternalID
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_login import Login, LoginError

from textwrap import dedent
import logging
from typing import Any, NamedTuple
from functools import cache, cached_property
import re
from time import sleep
from functools import wraps
from requests import JSONDecodeError
from os.path import expanduser, isfile
import json
from requests import Response
from unittest.mock import patch

logger = logging.getLogger(__name__)
logging.getLogger("wikibaseintegrator").setLevel(logging.ERROR)
re_sp = re.compile(r"\s+")


class IdMovie(NamedTuple):
    imdb: str
    filmaffinity: int


orig_response_json = requests.models.Response.json


def login_response_json(self: Response, *args, **kwargs):
    if self.status_code == 403:
        text = re_sp.sub(r" ", self.text).strip()
        raise LoginError(f"{self.status_code} {self.reason} {text}".strip())
    return orig_response_json(self, *args, **kwargs)


def get_config(file: str):
    path = expanduser(file)
    if not isfile(path):
        sys.exit(f"{file} no existe")
    with open(path, "r") as f:
        obj = json.load(f)
        if not isinstance(obj, dict):
            raise ValueError(f"{file} ha de ser un diccionario json")
        return obj


def _is_empty(x: Any):
    if x is None:
        return True
    if isinstance(x, (dict, list, tuple, set, str)):
        return len(x) == 0
    return False


def retry_until_stable(func):
    def __sort_kv(kv: tuple[Any, int]):
        k, v = kv
        arr = []
        arr.append(int(k is None))
        arr.append(-len(k) if isinstance(k, tuple) else 0)
        arr.append(-v)
        return tuple(arr)

    @wraps(func)
    def wrapper(*args, **kwargs):
        count = dict()
        while True:
            value = func(*args, **kwargs)
            count[value] = count.get(value, 1) + 1
            if count[value] > (1 + int(_is_empty(value))):
                return sorted(count.items(), key=__sort_kv)[0][0]
            if value is None:
                sleep(0.5 * count[value])
                continue
            sleep(0.1 * count[value])
    return wrapper


def log_if_empty(method):
    @wraps(method)
    def wrapper(self: "WikiApi", *args, **kwargs):
        val = method(self, *args, **kwargs)
        if _is_empty(val):
            logger.debug("Empty query:\n"+self.last_query)
        return val
    return wrapper


class WikiApi:
    WDT_IMDB = 'P345'
    WDT_FA = 'P480'

    def __init__(self, config: dict):
        self.__c = config
        self.__s = requests.Session()
        self.__user_agent = self.__c["user-agent"]
        self.__s.headers.update({
            "Accept": "application/sparql-results+json",
            "User-Agent": self.__user_agent
        })
        self.__last_query = None

    @property
    def last_query(self):
        return self.__last_query

    @cached_property
    def login(self):
        if None in (self.__c.get("user"), self.__c.get("password")):
            return None

        def new_session(*args, **kwargs):
            s = requests.Session(*args, **kwargs)
            s.headers.update({"User-Agent": self.__user_agent})
            return s

        with patch("requests.Session", return_value=new_session):
            with patch.object(requests.models.Response, "json", login_response_json):
                return Login(
                    user=self.__c["user"],
                    password=self.__c["password"],
                    user_agent=self.__user_agent
                )

    @cached_property
    def wbi(self):
        return WikibaseIntegrator(login=self.login)

    def get_property(self, qid: str, pid: str) -> tuple[str, ...]:
        qid = qid.rsplit("/", 1)[-1]
        return self.get_tuple(f'wd:{qid} wdt:{pid} ?field .')

    def set_property(self, qid: str, prop: str, value: str) -> str:
        qid = qid.rsplit("/", 1)[-1]
        item = self.wbi.item.get(entity_id=qid)
        if item.id != qid:
            raise ValueError(f"{item.id} != {qid}")
        statement = ExternalID(prop_nr=prop, value=str(value))
        item.claims.add(statement)
        item.write(allow_anonymous=self.login is None)
        return item.id

    def create_item(self, data: dict) -> str:
        claims: list[ExternalID] = list()
        for k, v in data.items():
            if not _is_empty(v):
                claims.append(ExternalID(prop_nr=k, value=str(v)))
        if len(claims) == 0:
            return None
        item = self.wbi.item.new()
        for c in claims:
            item.claims.add(c)
        new_item = item.write(allow_anonymous=self.login is None)
        return new_item.id

    def query_sparql(self, query: str) -> dict[str, Any]:
        # https://query.wikidata.org/
        query = dedent(query).strip()
        query = re.sub(r"\n(\s*\n)+", "\n", query)
        self.__last_query = query
        r = self.__s.get(
            "https://query.wikidata.org/sparql",
            params={"query": query}
        )
        try:
            r.raise_for_status()
        except Exception:
            logger.critical(f"Error ({r.status_code}) querying:\n"+query)
            raise
        try:
            return r.json()
        except JSONDecodeError:
            logger.critical("Error (no JSON format) querying:\n"+query)
            raise

    def query_bindings(self, query: str) -> list[dict[str, Any]]:
        data = self.query_sparql(query)
        bindings = data.get("results", {}).get("bindings", [])
        return bindings

    @cache
    @log_if_empty
    @retry_until_stable
    def get_tuple(self, query: str, limit: int = None):
        query = "SELECT ?field WHERE {\n%s\n}" % dedent(query)
        if limit:
            query += f"\nLIMIT {limit}"
        dt = self.query_bindings(query)
        arr = []
        for x in dt:
            if not x:
                continue
            i = x['field']['value']
            if not _is_empty(i) and i not in arr:
                arr.append(i)
        return tuple(arr)

    @cache
    def get(self, key: str, value: str, search: str):
        return self.get_tuple(
            """
            ?item wdt:%s "%s".
            OPTIONAL { ?item wdt:%s ?field . }
            """ % (key, value, search)
        )

    @cache
    def get_filmaffinity_from_imdb(self, id: str):
        arr: list[str] = []
        for v in self.get(WikiApi.WDT_IMDB, id, WikiApi.WDT_FA):
            try:
                f = float(v)
            except ValueError:
                logger.warning(f"imdb={id} filmaffinity={v}")
                continue
            i = int(v)
            if i != f or i < 1:
                logger.warning(f"imdb={id} filmaffinity={v}")
                continue
            if i not in arr:
                arr.append(i)
        return tuple(arr)

    @cache
    def get_imdb_from_filmaffinity(self, id: int):
        arr: list[int] = []
        for v in self.get(WikiApi.WDT_FA, id, WikiApi.WDT_IMDB):
            if not isinstance(v, str):
                logger.warning(f"filmaffinity={id} imdb={v}")
                continue
            if not re.match(r"^tt\d+$", v):
                logger.warning(f"filmaffinity={id} imdb={v}")
                continue
            if v not in arr:
                arr.append(v)
        return tuple(arr)

    def get_qid_by_property(self, prop: str, value: str | int) -> tuple[str, ...]:
        """
        Busca el QID del ítem que tiene la propiedad `prop` con valor `value`.
        """
        return self.get_tuple(f'?field wdt:{prop} "{value}".')


def get_ids(arr: list[str]):
    arr_imdb: list[str] = []
    arr_film: list[int] = []

    for i in arr:
        i = re.sub(r"^https://www.filmaffinity.com.*/film(\d+).html$", r"\1", i)
        i = re.sub(r"^https://www.imdb.com/.*/(tt\d+).*", r"\1", i)
        i = re.sub(r"^film(\d+)$", r"\1", i)
        if re.match(r"^tt\d+$", i) and i not in arr_imdb:
            arr_imdb.append(i)
        if i.isdigit():
            x = int(i)
            if x not in arr_film:
                arr_film.append(x)
            continue

    l1, l2 = map(len, (arr_imdb, arr_film))
    if l1 != l2 or 0 in (l1, l2):
        return None

    ids: set[IdMovie] = set()
    for id_imdb, id_film in zip(arr_imdb, arr_film):
        ids.add(IdMovie(
            imdb=id_imdb,
            filmaffinity=id_film
        ))

    return tuple(sorted(ids))


def set_id(WIKI: WikiApi, id: IdMovie):
    qid_imdb = WIKI.get_qid_by_property(WIKI.WDT_IMDB, id.imdb)
    qid_film = WIKI.get_qid_by_property(WIKI.WDT_FA, id.filmaffinity)

    qid_common = set(qid_imdb).intersection(qid_film)
    gid_need_imdb = set(qid_film).difference(qid_imdb)
    qid_need_film = set(qid_imdb).difference(qid_film)

    if len(qid_common):
        for qid in qid_common:
            print(f"[OK] {qid} ya relaciona {id.imdb} con {id.filmaffinity}")
        return True

    ko = False
    for qid in gid_need_imdb:
        for v in WIKI.get_property(qid, WIKI.WDT_IMDB):
            print(f"[KO] {qid} ya relaciona {id.filmaffinity} con {v}")
            ko = True
    for qid in qid_need_film:
        for v in WIKI.get_property(qid, WIKI.WDT_FA):
            print(f"[KO] {qid} ya relaciona {id.imdb} con {v}")
            ko = True

    if ko:
        return False

    for qid in qid_need_film:
        qid = WIKI.set_property(qid, WIKI.WDT_FA, id.filmaffinity)
        print(f"[OK] http://www.wikidata.org/entity/{qid} modificado para asociar {id.imdb} con {id.filmaffinity}")
    for qid in gid_need_imdb:
        qid = WIKI.set_property(qid, WIKI.WDT_IMDB, id.imdb)
        print(f"[OK] http://www.wikidata.org/entity/{qid} modificado para asociar {id.imdb} con {id.filmaffinity}")

    if (len(qid_need_film) + len(gid_need_imdb)) == 0:
        qid = WIKI.create_item({
            WIKI.WDT_FA: id.filmaffinity,
            WIKI.WDT_IMDB: id.imdb
        })
        if qid is None:
            print(f"No se ha podido crear el elemento para <{id.imdb}, {id.filmaffinity}>")
            return False
        print(f"[OK] http://www.wikidata.org/entity/{qid} creado para asociar {id.imdb} con {id.filmaffinity}")

    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Asocia ids de IMDb con ids de FilmAffinity a traves de WikiData'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='fichero de configuración',
        default='~/wikidata.json'
    )
    parser.add_argument("ids", nargs='+', help="IDs de IMDb y FilmAffinity")
    pargs = parser.parse_args()
    ids = get_ids(pargs.ids)
    if ids is None or len(ids) == 0:
        sys.exit("Los ids no cumplen el formato: " + ", ".join(pargs.ids))

    WIKI = WikiApi(get_config(pargs.config))

    ko = False
    for id in ids:
        if set_id(WIKI, id) is False:
            ko = False
    if ko is False:
        sys.exit(1)
