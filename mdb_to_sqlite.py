#!/usr/bin/env python3

import os
import sqlite3
import subprocess
import sys
import argparse
import logging
import re

def save(sql_script, out, save_sql=False):
    logging.info("Guardando resultado")
    sqlite = out+".sqlite"
    if os.path.isfile(sqlite):
        os.remove(sqlite)
    con = sqlite3.connect(sqlite)
    c = con.cursor()
    c.executescript(sql_script)
    con.commit()
    c.close()
    if save_sql:
        with open(out+".sql", "w") as f:
            f.write(sql_script)

def run_cmd(*args):
    logging.debug("$ "+" ".join("'"+a+"'" if ' ' in a else a for a in args))
    output = subprocess.check_output(args)
    output = output.decode(sys.stdout.encoding)
    lines = list(l for l in output.strip().split('\n') if l.strip())
    logging.debug("> %s líneas", len(lines))
    return output

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
    # Get the list of table names with "mdb-tables"
    tables = run_cmd("mdb-tables", "-1", file)
    tables = [t for t in tables.split("\n") if len(t.strip()) > 0]

    # start a transaction, speeds things up when importing
    sql_script = 'BEGIN;'

    # Dump each table as a CSV file using "mdb-export",
    # converting " " in table names to "_" for the CSV filenames.
    for table in tables:
        logging.info("Generando inserts: %s", table)
        output = run_cmd("mdb-export", "-I", "sqlite", "-D", "%Y-%m-%d %H:%M", file, table)
        sql_script = sql_script + '\n' + output

    sql_script = sql_script + "\nCOMMIT;"  # end the transaction

    return sql_script


def mdb_to_sqlite(DATABASE):
    SQL_SCRIPT = get_schema(DATABASE) + '\n' + get_inserts(DATABASE)
    save(SQL_SCRIPT, DATABASE)


if __name__ == "__main__":
    EXT=("mdb", "accdb")
    parser = argparse.ArgumentParser("Convierte una base de datos Access ({}) a SQLite".format("|".join(EXT)))
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

    mdb_to_sqlite(args.mdb)
