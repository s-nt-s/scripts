#!/usr/bin/python3

import argparse
import email
import imaplib
import os
import sys
from email.header import decode_header
from getpass import getpass
import yaml
import re


parser = argparse.ArgumentParser(description="Download attachments from IMAP")
parser.add_argument("config", help="Config Yaml File")
parser.add_argument('--create', action='store_true', help='Create an example config file')
args = parser.parse_args()

if args.create:
    if os.path.isfile(args.config):
        sys.exit(args.config+" it already exists")
    with open(args.config, 'w') as f:
        f.write(r'''user: my@mail.com
pass: ******
imap: imap.mail.com
label: Trabajo/Nomina
out: '.'
lower: true
match: '.*20\d\d\.pdf'
subs:
  - ['.* (\S+) (20\d\d)\.pdf', '\2.\1.pdf']
  - ['\b(enero)\b',      '01']
  - ['\b(febrero)\b',    '02']
  - ['\b(marzo)\b',      '03']
  - ['\b(abril)\b',      '04']
  - ['\b(mayo)\b',       '05']
  - ['\b(junio)\b',      '06']
  - ['\b(julio)\b',      '07']
  - ['\b(agosto)\b',     '08']
  - ['\b(septiembre)\b', '09']
  - ['\b(octubre)\b',    '10']
  - ['\b(noviembre)\b',  '11']
  - ['\b(diciembre)\b',  '12']
''')
    sys.exit()

if not os.path.isfile(args.config):
    sys.exit(args.config+" doesn't exist")

with open(args.config, 'r') as f:
    config = yaml.load(f)

if "out" in config:
    c = os.path.abspath(args.config)
    p = os.path.dirname(c)
    p = os.path.join(p, config["out"])
    config["out"] = os.path.normpath(p)
else:
    config["out"] = input('Enter where do you want to place the attachments: ')

if not os.path.isdir(config["out"]):
    sys.exit(config["out"]+" isn't a directory")

if "imap" not in config:
    config["imap"] = input('Enter your IMAP server: ')
if "user" not in config:
    config["user"] = input('Enter your IMAP username: ')
if "pass" not in config:
    config["pass"] = getpass('Enter your password: ')

if "match" in config:
    config["match"] = re.compile(config["match"])

if "subs" in config:
    for sub in config["subs"]:
        sub[0] = re.compile(sub[0])

imapSession = imaplib.IMAP4_SSL(config["imap"])
typ, accountDetails = imapSession.login(config["user"], config["pass"])
if typ != 'OK':
    print ('Not able to sign in!')
    raise

if "label" in config:
    imapSession.select(config["label"])

typ, data = imapSession.search(None, 'ALL')
if typ != 'OK':
    print ('Error searching Inbox.')
    raise

# Iterating over all emails
for msgId in data[0].split():
    typ, messageParts = imapSession.fetch(msgId, '(RFC822)')
    if typ != 'OK':
        print ('Error fetching mail.')
        raise

    emailBody = messageParts[0][1]
    mail = email.message_from_bytes(emailBody)

    for part in mail.walk():
        if part.get_content_maintype() == 'multipart':
            continue
        if part.get('Content-Disposition') is None:
            continue
        fileName = part.get_filename()

        if bool(fileName):
            fileName = decode_header(fileName)[0][0]
            if not isinstance(fileName, str):
                fileName = str(fileName, 'utf-8')
            old_fileName = fileName
            
            if config.get("lower", False):
                fileName = fileName.lower()

            if "match" in config and not config["match"].match(fileName):
                continue

            if "subs" in config:
                for sub in config["subs"]:
                    fileName = sub[0].sub(sub[1], fileName)
            
            filePath = os.path.join(config["out"], fileName)
            if not os.path.isfile(filePath):
                if old_fileName == fileName:
                    print (fileName)
                else:
                    print (old_fileName+" -> "+fileName)

                fp = open(filePath, 'wb')
                fp.write(part.get_payload(decode=True))
                fp.close()

imapSession.close()
imapSession.logout()
