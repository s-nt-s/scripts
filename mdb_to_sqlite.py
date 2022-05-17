#!/usr/bin/env python3

import os
import sqlite3
import subprocess
import sys
import argparse
import logging


import logging
import threading
import subprocess


class LogPipe(threading.Thread):

    def __init__(self, level):
        super().__init__()
        self.daemon = False
        self.level = level
        self.fdRead, self.fdWrite = os.pipe()
        self.pipeReader = os.fdopen(self.fdRead)
        self.start()

    def __enter__(self, *args, **kwargs):
        return self

    def __exit__(self, *args, **kwargs):
        return self.close()

    def fileno(self):
        return self.fdWrite

    def run(self):
        for line in iter(self.pipeReader.readline, ''):
            logging.log(self.level, line.strip('\n'))
        self.pipeReader.close()

    def close(self):
        os.close(self.fdWrite)


def run_cmd(*args):
    logging.debug("$ "+" ".join(map(prs_arg, args)))
    with LogPipe(logging.ERROR) as logpipe:
        output = subprocess.check_output(args, stderr=logpipe)
        output = output.decode(sys.stdout.encoding)
    lines = len(list(l for l in output.strip().split('\n') if l.strip()))
    if lines == 1:
        logging.debug("> 1 línea")
    else:
        logging.debug("> %s líneas", lines)
    return output


def to_dump(prefix, *sql_script, save_sql=False):
    logging.info("Creando .sqlite")
    sqlite = prefix+".sqlite"
    if os.path.isfile(sqlite):
        os.remove(sqlite)
    sql_script = "\n".join(sql_script)
    con = sqlite3.connect(sqlite)
    c = con.cursor()
    c.executescript(sql_script)
    con.commit()
    c.close()
    if save_sql:
        logging.info("Creando .sql")
        with open(prefix+".sql", "w") as f:
            f.write(sql_script)


def prs_arg(arg):
    if isinstance(arg, str) and " " in arg:
        return "'"+arg+"'"
    return arg


def get_schema(file):
    logging.info("Generando esquema")
    schema = run_cmd("mdb-schema", file, "sqlite")
    for line in schema.split("\n"):
        line = line.strip()
        if line.startswith("ALTER TABLE ") and "ADD CONSTRAINT" in line:
            return run_cmd("mdb-schema", "--no-relations", file, "sqlite")
    return schema


def get_inserts(file):
    logging.debug("Obteniendo tablas")
    tables = run_cmd("mdb-tables", "-1", file)
    tables = [t for t in tables.split("\n") if len(t.strip()) > 0]

    sql_script = 'BEGIN;'

    for table in tables:
        logging.info("Generando inserts: %s", table)
        output = run_cmd("mdb-export", "-I", "sqlite", "-D", "%Y-%m-%d %H:%M", file, table)
        if len(output.strip()) > 0:
            sql_script = sql_script + '\n' + output

    sql_script = sql_script + "\nCOMMIT;"

    return sql_script


def mdb_to_sqlite(mdb, save_sql=False):
    to_dump(
        mdb,
        get_schema(mdb),
        get_inserts(mdb),
        save_sql=save_sql
    )


if __name__ == "__main__":
    EXT = ("mdb", "accdb")
    parser = argparse.ArgumentParser("Convierte una base de datos Access ({}) a SQLite".format("|".join(EXT)))
    parser.add_argument('--sql', action='store_true', help="Guardar script sql")
    parser.add_argument('--verbose', '-v', action='count', help="Nivel de depuración", default=0)
    parser.add_argument('mdb', help='Base de datos Access ({})'.format("|".join(EXT)))
    args = parser.parse_args()

    levels = [logging.INFO, logging.DEBUG]
    level = min(len(levels)-1, args.verbose)

    logging.basicConfig(
        level=levels[level],
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%M-%d %H:%M:%S'
    )

    if not os.path.isfile(args.mdb):
        sys.exit(args.mdb+" no existe")
    ext = args.mdb.split(".")[-1].lower()
    if ext not in EXT:
        sys.exit(args.mdb+" no termina en .mdb o .accdb")

    mdb_to_sqlite(args.mdb, save_sql=args.sql)
