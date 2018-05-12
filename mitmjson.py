import os
import json
from mitmproxy.net.http import cookies
from urllib.parse import urlparse
from datetime import datetime
import sys

def get_json(text):
    if text:
        try:
            return json.loads(text)
        except Exception as e:
            pass
    return None

def format_request_cookies(fields):
    return format_cookies(cookies.group_cookies(fields))

def format_response_cookies(fields):
    return format_cookies((c[0], c[1][0], c[1][1]) for c in fields)

def format_cookies(cookie_list):
    rv = []

    for name, value, attrs in cookie_list:
        cookie_har = {
            "name": name,
            "value": value,
        }

        for key in ("path", "domain", "comment"):
            if key in attrs:
                cookie_har[key] = attrs[key]


        rv.append(cookie_har)

    return rv

def name_value(obj):
    r = {}
    for k, v in obj.items():
        r[k] = v
    return r

def get_lines(txt):
    if os.path.isfile(txt):
        with open(txt, 'r') as f:
            return [l.strip() for l in f.readlines() if len(l.strip())>0]
    return []

def get_avoid(hostname):
    return get_lines("avoid.txt") + get_lines(hostname + "/avoid.txt")

def response(flow):
    uparse = urlparse(flow.request.url)
    
    if not uparse.hostname:
        print(flow.request.url)
        return

    if flow.request.url in get_avoid(uparse.hostname):
        return
    
    js = get_json(flow.response.get_text(strict=False))
    if not js:
        return

    if uparse.hostname not in os.listdir("."):
        print(flow.request.url)
        return

    req_cookies = format_request_cookies(flow.request.cookies.fields)
    res_cookies = format_response_cookies(flow.response.cookies.fields)
    req_content_type = flow.request.headers.get("Content-Type", None)
    res_content_type = flow.response.headers.get("Content-Type", None)
    res_redirect = flow.response.headers.get('Location', None)
    
    info = {
        "request": {
            "method": flow.request.method,
            "url": flow.request.url,
            "headers": name_value(flow.request.headers),
        },
        "response": {
            "status": flow.response.status_code,
            "statusText": flow.response.reason,
            "headers": name_value(flow.response.headers),
            "json": js
        }
    }

    if len(req_cookies)>0:
        info["request"]["cookies"]=req_cookies
    if len(res_cookies)>0:
        info["response"]["cookies"]=res_cookies
    if res_content_type:
        info["response"]["mimeType"]=res_content_type
    if res_redirect:
        info["response"]["redirectURL"]=res_redirect
    
    if flow.request.method in ("POST", "PUT", "PATCH"):
        req_params = {}
        for a, b in flow.request.urlencoded_form.items(multi=True):
            req_params[a] = b
        req_text = flow.request.get_text(strict=False)
        req_json = get_json(req_text)
        postData = {}
        if req_content_type:
            postData["mimeType"] = req_content_type
        if len(req_params)>0:
            postData["params"] = req_params
        if req_json:
            postData["json"] = req_json
        elif req_text:
            postData["text"] = req_text
        info["request"]["postData"] = postData

    name = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    if uparse.path:
        name = name + uparse.path.replace("/", ".")
    name = uparse.hostname+"/"+name + ".json"
    print(flow.request.url + " ---> "+name)
    with open(name, "w") as f:
        f.write(json.dumps(info, indent=4, sort_keys=True))
