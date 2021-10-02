#!/usr/bin/python3

import os
import sqlite3
import subprocess
import sys
import argparse
import logging
from textwrap import dedent
import re

re_not_null = re.compile(r"\s*\bNOT NULL(,)?")

def save(sql_script, out):
    with open(out+"sql", "w") as f:
        f.write(sql_script)
    sqlite = out+"sqlite"
    if os.path.isfile(sqlite):
        os.remove(sqlite)
    con = sqlite3.connect(sqlite)
    c = con.cursor()
    c.executescript(sql_script)
    con.commit()
    c.close()

def run_cmd(*args):
    output = subprocess.check_output(args)
    output = output.decode('utf-8')
    return output

def get_schema(db):
    schema = run_cmd("mdb-schema", db, "sqlite")
    for line in schema.split("\n"):
        line = line.strip()
        if line.startswith("ALTER TABLE ") and "ADD CONSTRAINT" in line:
            return run_cmd("mdb-schema", "--no-relations", db, "sqlite")
    return schema


def mdb_to_sqlite(DATABASE):
    # Dump the schema for the DB
    SQL_SCRIPT = get_schema(DATABASE)

    # Get the list of table names with "mdb-tables"
    tables = run_cmd("mdb-tables", "-1", DATABASE)
    tables = tables.split("\n")

    # start a transaction, speeds things up when importing
    SQL_SCRIPT = SQL_SCRIPT + '\nBEGIN;'

    # Dump each table as a CSV file using "mdb-export",
    # converting " " in table names to "_" for the CSV filenames.
    for table in tables:
        if len(table) > 0:
            output = run_cmd("mdb-export", "-I", "sqlite", "-D", "%Y-%m-%d %H:%M", DATABASE, table)
            SQL_SCRIPT = SQL_SCRIPT + '\n' + output

    SQL_SCRIPT = SQL_SCRIPT + "\nCOMMIT;"  # end the transaction

    NAME = DATABASE[:-3]
    save(SQL_SCRIPT, NAME)


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Convierte una base de datos Access (mdb) a SQLite")
    parser.add_argument('--verbose', '-v', action='count', help="Nivel de depuración", default=0)
    parser.add_argument('mdb', help='Base de datos Access (mdb)')
    args = parser.parse_args()

    if args.verbose:
        levels = [logging.INFO, logging.DEBUG]
        main_level = min(len(levels)-1, args.verbose-1)
        alte_level = min(len(levels)-1, args.verbose-2)

        logging.basicConfig(
            level=levels[main_level],
            format='%(asctime)s %(name)s - %(levelname)s - %(message)s',
            datefmt='%d-%b-%y %H:%M:%S'
        )

    if not os.path.isfile(args.mdb):
        sys.exit(args.mdb+" no existe")
    if not args.mdb.endswith(".mdb"):
        sys.exit(args.mdb+" no termina en .mdb")

    mdb_to_sqlite(args.mdb)
