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

def safe_save(sql_script, out):
    try:
        save(sql_script, out)
    except sqlite3.IntegrityError as e:
        logging.info("Reintento con ignore_check_constraints para evitar error "+str(e))
        sql_script=dedent("""
            -- ----------------------------------------------------------
            -- 'NOT NULL' comentados y constraints deshabilitadas
            -- para evitar error:
            --   {}
            -- ----------------------------------------------------------
            PRAGMA ignore_check_constraints = on;
            PRAGMA foreign_keys = off;
            """).lstrip().format(str(e))+ "\n"+ \
            re_not_null.sub(r"\1 -- NOT NULL\1", sql_script)
        save(sql_script, out)

def run_cmd(*args):
    output = subprocess.check_output(args)
    output = output.decode('utf-8')
    return output


def mdb_to_sqlite(DATABASE):
    # Dump the schema for the DB
    SQL_SCRIPT = run_cmd("mdb-schema", DATABASE, "mysql")

    # Get the list of table names with "mdb-tables"
    table_names = subprocess.Popen(["mdb-tables", "-1", DATABASE],
                                   stdout=subprocess.PIPE).communicate()
    table_names = table_names[0]
    tables = table_names.splitlines()

    # start a transaction, speeds things up when importing
    SQL_SCRIPT = SQL_SCRIPT + '\nBEGIN;'

    # Dump each table as a CSV file using "mdb-export",
    # converting " " in table names to "_" for the CSV filenames.
    for table in tables:
        if len(table) > 0:
            output = run_cmd("mdb-export", "-I", "mysql", DATABASE, table)
            SQL_SCRIPT = SQL_SCRIPT + '\n' + output

    SQL_SCRIPT = SQL_SCRIPT + "\nCOMMIT;"  # end the transaction

    NAME = DATABASE[:-3]
    safe_save(SQL_SCRIPT, NAME)


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
