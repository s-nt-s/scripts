#!/usr/bin/python3
import sys
import email
from email.parser import Parser
from email.header import decode_header
from email.message import Message
from functools import cached_property
import json


class Mail:
    def __init__(self, msg: Message):
        self.msg = msg

    @cached_property
    def attachments(self):
        atts = {}
        for part in self.msg.walk():
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                continue
            file_name = part.get_filename()

            if bool(file_name):
                file_name = decode_header(file_name)[0][0]
                if not isinstance(file_name, str):
                    file_name = str(file_name, 'utf-8', 'ignore')
                body_bytes = part.get_payload(decode=True)
                atts[file_name] = self.__read_file(file_name, body_bytes)
        return atts
    
    @cached_property
    def body(self):
        if not self.msg.is_multipart():
            # extract content type of email
            content_type = self.msg.get_content_type()
            # get the email body
            body = self.msg.get_payload(decode=True).decode()
            if content_type == "text/plain":
                return body.rstrip()
            return

        # iterate over email parts
        for part in self.msg.walk():
            # extract content type of email
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition"))

            try:
                body = part.get_payload(decode=True).decode()
            except:
                continue
            if content_type == "text/plain" and "attachment" not in content_disposition:
                return body.rstrip()
    
    def __read_file(self, name, body_bytes):
        ext = name.rsplit(".")[-1].lower()
        if ext == "json":
            body = body_bytes.decode('utf8')
            return json.loads(body)
        return body_bytes

mail = Mail(Parser().parse(sys.stdin))
