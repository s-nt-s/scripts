#!/usr/bin/python3

import argparse
import email
import imaplib
import os
import sys
from email.header import decode_header
from getpass import getpass
import yaml
from xmppbot.xmppmsg import XmppMsg


parser = argparse.ArgumentParser(description="Read mail and send by XMPP")
parser.add_argument("config", nargs='?', help="Config Yaml File")
parser.add_argument('--example', action='store_true', help='Show an example config file')
args = parser.parse_args()

if args.example:
    print("#!"+os.path.abspath(__file__)+'''
mail:
    user: my@mail.com
    pass: ******
    imap: imap.mail.com
    label: xmpp
xmpp:
    user: my@xmpp.com
    pass: ******
    to: to@xmpp.com
'''.rstrip())
    sys.exit()

if not args.config:
    sys.exit("config arguments are required when --example is not present")

if not os.path.isfile(args.config):
    sys.exit(args.config+" doesn't exist")

with open(args.config, 'r') as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

xsend = XmppMsg(config=config['xmpp'])
xsend.to = config['xmpp']['to']

def get_text(response):
    msg = email.message_from_bytes(response[1])

    if not msg.is_multipart():
        # extract content type of email
        content_type = msg.get_content_type()
        # get the email body
        body = msg.get_payload(decode=True).decode()
        if content_type == "text/plain":
            return body
        return

    # iterate over email parts
    for part in msg.walk():
        # extract content type of email
        content_type = part.get_content_type()
        content_disposition = str(part.get("Content-Disposition"))

        try:
            body = part.get_payload(decode=True).decode()
        except:
            continue
        if content_type == "text/plain" and "attachment" not in content_disposition:
            return body


imapSession = imaplib.IMAP4_SSL(config['mail']["imap"])
typ, accountDetails = imapSession.login(config['mail']["user"], config['mail']["pass"])
if typ != 'OK':
    raise Exception('Not able to sign in!')


typ, data = imapSession.select(config['mail'].get("label", "INBOX"))
if typ != 'OK':
    raise Exception(str(data[0], 'utf-8'))


typ, data = imapSession.search(None, 'ALL')
if typ != 'OK':
    raise Exception('Error searching Inbox.')


# Iterating over all emails
for msgId in data[0].split():
    typ, messageParts = imapSession.fetch(msgId, '(RFC822)')
    if typ != 'OK':
        raise Exception('Error fetching mail.')

    body = get_text(messageParts[0])
    xsend.msg = body

xsend.send()

imapSession.close()
imapSession.logout()
