#!/usr/bin/env python3

import argparse
import hashlib
import os
import shutil
import sqlite3
import sys
import re
from pathlib import Path
import tempfile
from typing import Callable, NamedTuple, TypeVar
from zipfile import ZipFile, is_zipfile
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")

T = TypeVar("T")

KO = (None, 0, '0')
MODES = ("all", "progress", "bookmarks", "words", "activity", "events")


class Activity(NamedTuple):
    Id: str
    Enabled: bool
    Type: str
    Action: int
    Date: str
    Data: bytes


class Bookmark(NamedTuple):
    BookmarkID: str
    VolumeID: str
    ContentID: str
    StartContainerPath: str
    StartContainerChildIndex: str
    StartOffset: str
    EndContainerPath: str
    EndContainerChildIndex: str
    EndOffset: str
    Text: str
    Annotation: str
    ExtraAnnotationData: str
    DateCreated: str
    ChapterProgress: str
    Hidden: str
    Version: str
    DateModified: str
    Creator: str
    UUID: str
    UserID: str
    SyncTime: str
    Published: str
    ContextString: str
    Type: str


class WordItem(NamedTuple):
    Text: str
    VolumeId: str
    DictSuffix: str
    DateCreated: str


class Book(NamedTuple):
    ContentID: str
    BookID: str
    Title: str
    ISBN: str
    MimeType: str
    ContentType: int
    ReadStatus: int
    PercentRead: int
    DateLastRead: str
    ChapterIDBookmarked: str
    ParagraphBookmarked: int
    BookmarkWordOffset: int
    FirstTimeReading: str
    WordCount: str
    RestOfBookEstimate: str
    CurrentChapterEstimate: str
    CurrentChapterProgress: str
    PocketStatus: str
    DateAdded: str
    TimesStartedReading: str
    TimeSpentReading: str
    LastTimeStartedReading: str
    LastTimeFinishedReading: str
    bookmarks: tuple[Bookmark, ...] = tuple()
    wordList: tuple[WordItem, ...] = tuple()


def unzip_if_needed(path: Path) -> Path:
    path = Path(path).expanduser().resolve()
    if not is_zipfile(path):
        return path

    digest = hashlib.sha256(str(path).encode("utf-8")).hexdigest()
    extracted_path = Path("/tmp") / f"{digest}.sqlite"
    if extracted_path.is_file():
        return extracted_path

    temporary_path = None
    with ZipFile(path) as archive:
        database = archive.open(".kobo/KoboReader.sqlite")
        with database, tempfile.NamedTemporaryFile(
            mode="wb",
            dir=extracted_path.parent,
            prefix=f".{extracted_path.name}.",
            suffix=".tmp",
            delete=False,
        ) as output:
            temporary_path = Path(output.name)
            shutil.copyfileobj(database, output)

    os.replace(temporary_path, extracted_path)

    return extracted_path


class Db:
    def __init__(self, db_path: str | Path, readonly: bool = False):
        self.__db_path = Path(db_path).expanduser().absolute().resolve()
        if not self.__db_path.is_file():
            raise FileNotFoundError(f"Archivo de base de datos no encontrado: {self.__db_path}")
        if readonly:
            self.__db_path = unzip_if_needed(self.__db_path)
            self.__conn = sqlite3.connect(f"{self.__db_path.as_uri()}?mode=ro", uri=True)
        else:
            self.__conn = sqlite3.connect(str(self.__db_path))
        self.__conn.row_factory = sqlite3.Row
        self.__cursor = self.__conn.cursor()
        self.__readonly = readonly

    @property
    def path(self) -> Path:
        return self.__db_path

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def execute(self, query, params=None):
        if params is None:
            params = []
        self.__cursor.execute(query, params)
        self.__conn.commit()

    def fetchall(self, query: str, *params) -> list[sqlite3.Row]:
        self.__cursor.execute(query, list(params))
        try:
            return self.__cursor.fetchall()
        except Exception as e:
            logger.critical(f"{e}\n{self.__db_path}\n{params}\n{query}")
            raise e

    def count(self, query: str, *params) -> int:
        vals = self.fetchall(f"select count(*) total from {query}", *params)
        return vals[0]['total']

    def get(
        self,
        cst: Callable[..., T],
        query: str,
        *params: object,
    ) -> tuple[T, ...]:
        return tuple(cst(**i) for i in self.fetchall(query, *params))

    def get_activity(self):
        return self.get(
            Activity,
            """
            SELECT distinct Id, Enabled, Type, Action, Date, CAST(Data AS BLOB) AS Data
            FROM Activity
            """,
        )

    def close(self):
        self.__conn.close()

    def get_bookmarks(self, VolumeID: str):
        sql = '''
            SELECT
                BookmarkID,
                VolumeID,
                ContentID,
                StartContainerPath,
                StartContainerChildIndex,
                StartOffset,
                EndContainerPath,
                EndContainerChildIndex,
                EndOffset,
                Text,
                Annotation,
                ExtraAnnotationData,
                DateCreated,
                ChapterProgress,
                Hidden,
                Version,
                DateModified,
                Creator,
                UUID,
                UserID,
                SyncTime,
                Published,
                ContextString,
                Type
            FROM
                Bookmark
            WHERE VolumeID = ?
        '''
        return self.get(Bookmark, sql, VolumeID)

    def get_books(self, where: str = None):
        sql = '''
            SELECT
                ContentID,
                ContentType,
                MimeType,
                BookID,
                Title,
                DateLastRead,
                FirstTimeReading,
                ChapterIDBookmarked,
                ParagraphBookmarked,
                BookmarkWordOffset,
                ReadStatus,
                "___PercentRead" AS PercentRead,
                ISBN,
                WordCount,
                RestOfBookEstimate,
                CurrentChapterEstimate,
                CurrentChapterProgress,
                PocketStatus,
                DateAdded,
                TimesStartedReading,
                TimeSpentReading,
                LastTimeStartedReading,
                LastTimeFinishedReading
            FROM
                content
            WHERE ContentType = 6
        '''
        where = (where or '').strip()
        if where:
            sql += f" AND {where}"
        books: list[Book] = []
        for row in self.fetchall(sql):
            b = Book(
                **row,
            )
            b = b._replace(
                bookmarks=self.get_bookmarks(b.ContentID),
                wordList=self.get(
                    WordItem,
                    '''
                    SELECT
                        Text,
                        VolumeId,
                        DictSuffix,
                        DateCreated
                    FROM
                        WordList
                    WHERE VolumeId = ?
                    ''',
                    b.ContentID
                )
            )
            books.append(b)
        return tuple(books)

    def find_book(self, book: Book):
        for rslt in (
            f'ContentID = "{book.ContentID}"',
            f'ContentID like "%/{book.ContentID.split("/")[-1]}"',
        ):
            books = self.get_books(f'{rslt} AND MimeType = "{book.MimeType}"')
            if len(books) == 1:
                return books[0]
            if len(books) > 1:
                logger.warning(f"Se encontraron {len(books)} libros que cumple {rslt}")

    def update(self, table: str, where: str, **kwargs):
        if not kwargs or self.__readonly:
            return
        sql = f'''
            UPDATE {table}
            SET {', '.join(f"{k} = ?" for k in kwargs.keys())}
            WHERE {where}
        '''
        self.execute(sql, list(kwargs.values()))

    def insert(self, table: str, **kwargs):
        if not kwargs or self.__readonly:
            return
        sql = f'''
            INSERT INTO {table} ({', '.join(kwargs.keys())})
            VALUES ({', '.join('?' for _ in kwargs)})
        '''
        self.execute(sql, list(kwargs.values()))

    def __build_book_update(self, source: Book, target: Book):
        update_sql = {}
        #if target.DateLastRead is not None and (source.DateLastRead is None or source.DateLastRead<target.DateLastRead):
        #    return update_sql
        s = source._asdict()
        t = target._asdict()
        for k, v in s.items():
            if v is None or isinstance(v, tuple):
                continue
            if k in ('ContentID', 'BookID', 'Title', 'ISBN', 'MimeType', 'ContentType'):
                continue
            old = t[k]
            if v == old:
                continue
            #if old is not None:
            #    if k == "DateLastRead" and old > v:
            #        continue
            k = {
                'PercentRead': '___PercentRead'
            }.get(k, k)
            update_sql[k] = v
        return update_sql

    def __build_word_insert(self, source: Book, target: Book):
        words: list[WordItem] = []
        ok = set(w.Text for w in source.wordList).difference(
            set(w.Text for w in target.wordList)
        )
        for i in source.wordList:
            if i.Text in ok:
                words.append(i)
        return tuple(words)

    def __build_word_bookmarks(self, source: Book, target: Book):
        bookmarks: list[Bookmark] = []
        ok = set(b.BookmarkID.strip() for b in source.bookmarks).difference(
            set(b.BookmarkID.strip() for b in target.bookmarks)
        )
        for b in source.bookmarks:
            if b.BookmarkID.strip() in ok:
                bookmarks.append(b)
        return tuple(bookmarks)

    def sync(self, source: Book, target: Book, mode: str = "all"):
        update_sql = self.__build_book_update(source, target) if mode in ('all', 'progress') else {}
        words = self.__build_word_insert(source, target) if mode in ('all', 'words') else tuple()
        bookmarks = self.__build_word_bookmarks(source, target) if mode in ('all', 'bookmarks') else tuple()

        if not update_sql and not words and not bookmarks:
            return

        logger.info(f"_____________________________________")
        logger.info(f"### {source.ContentID} {source.Title}")

        if update_sql:
            self.update('content', f'ContentID = "{target.ContentID}"', **update_sql)
            logger.info(f"  UPDATE: {update_sql}")

        for i in words:
            i = i._replace(VolumeId=target.ContentID)
            self.insert('WordList', **i._asdict())
            logger.info(f"  INSERT Word: {i.Text}")

        max_log_length = 20
        for b in bookmarks:
            b = b._replace(VolumeID=target.ContentID)
            self.insert('Bookmark', **b._asdict())
            txt = re.sub(r"\n.*", "", (b.Text or '')).strip()
            if len(txt) > max_log_length:
                txt = txt[:max_log_length].strip() + "..."
            logger.info(f"  INSERT Bookmark: {b.BookmarkID} {txt}")

    def migrate(self, table: str, source: "Db"):
        if self.__readonly:
            return

        src = '"SRC"'
        self.__conn.execute(
            f"ATTACH DATABASE ? AS {src}",
            (str(source.path),),
        )
        cursor = self.__conn.execute(
            f"INSERT OR IGNORE INTO {table} "
            f"SELECT * FROM {src}.{table}"
        )
        self.__conn.commit()
        self.__conn.execute(f"DETACH DATABASE {src}")
        if cursor.rowcount:
            logger.info(
                "Migrated %s rows from %s (%s)",
                cursor.rowcount,
                table,
                source.path,
            )


def do_sync(source: str, target: str, apply: bool, mode: str):
    book_pair: tuple[Book, Book] = []
    with Db(target, readonly=not apply) as target_db:
        with Db(source, readonly=True) as source_db:
            for b in source_db.get_books():
                if len(b.bookmarks) == 0 and len(b.wordList) == 0 and (
                    b.ReadStatus in KO or (
                        b.ReadStatus == 1 and
                        b.PercentRead in KO and
                        b.ChapterIDBookmarked in KO and
                        b.BookmarkWordOffset in KO
                    )
                ):
                    continue
                n = target_db.find_book(b)
                if not n:
                    #logger.warning(f"Libro no encontrado: {b.ContentID}, {b.Title}")
                    continue
                book_pair.append((b, n))
            if mode in ('all', 'events'):
                target_db.migrate("Event", source_db)
            #for a in source_db.get_activity():
            #    if 0 == target_db.count("activity where Id IS ? and Type IS ? and Date = ?", a.Id, a.Type, a.Date):
            #        target_db.insert("activity", **a._asdict())
        for b, n in book_pair:
            target_db.sync(b, n, mode)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Migra anotaciones y progreso entre dos Kobo."
        )
    )
    parser.add_argument(
        "--source",
        required=True,
        nargs='+',
        help="KoboReader.sqlite de origen (p. ej. Clara HD)",
    )
    parser.add_argument(
        "--target",
        required=True,
        help="KoboReader.sqlite de destino (p. ej. Clara BW)",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Ejecutar la migración; sin esto solo simula.",
    )

    parser.add_argument(
        "--mode",
        type=str,
        choices=MODES,
        default=MODES[0],
        help=f"Tipo de actualización ({', '.join(MODES)}). Por defecto: {MODES[0]}.",
    )

    args = parser.parse_args()
    sources = sorted(
        map(Path, args.source),
        key=lambda p: p.stat().st_mtime
    )

    for source in sources:
        dt = datetime.fromtimestamp(
            source.stat().st_mtime
        ).strftime("%Y-%m-%d %H:%M")
        logger.info(f"{dt} {source}")
        do_sync(source, args.target, args.apply, args.mode)

    return 0


if __name__ == "__main__":
    sys.exit(main())
