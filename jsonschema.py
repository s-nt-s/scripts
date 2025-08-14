#!/usr/bin/env python3

import json
import re
import argparse
from genson import SchemaBuilder


def _complete_schema(schema: dict, obj: list, threshold=60):
    if not isinstance(obj, list):
        return schema
    obj = [o for o in obj if o is not None]
    if len(obj) == 0:
        return schema
    schema_type = schema['type']
    typ = None
    hasNull = None
    if isinstance(schema_type, str):
        typ = schema_type
        hasNull = False
    elif isinstance(schema_type, list):
        st = tuple(sorted((s for s in schema_type if s not in ("null", None))))
        hasNull = len(st) < len(schema_type)
        if len(st) == 1:
            typ = st[0]
    if typ == 'object':
        for k, v in list(schema['properties'].items()):
            schema['properties'][k] = _complete_schema(v, [o.get(k) for o in obj], threshold=threshold)
        return schema
    if typ == 'array':
        lns: set[int] = set()
        arr = []
        for i in obj:
            lns.add(len(i))
            arr = arr + i
        schema['items'] = _complete_schema(schema['items'], arr, threshold=threshold)
        schema['minItems'] = min(lns)
        schema['maxItems'] = max(lns)
        return schema
    if typ not in ('string', 'integer', 'boolean'):
        return schema
    vals = sorted(set(obj))
    if len(vals) == 1 and not hasNull:
        schema.clear()
        schema['const'] = vals[0]
        return schema
    if len(vals) == 0 and hasNull:
        schema.clear()
        schema['const'] = None
        return schema
    if len(vals) <= threshold:
        if hasNull:
            vals.insert(0, None)
        schema['enum'] = vals
        return schema
    if typ == 'integer':
        schema['minimum'] = vals[0]
        schema['maximum'] = vals[-1]
    if typ == 'string':
        lvls = sorted(map(len, vals))
        schema['minLength'] = lvls[0]
        schema['maxLength'] = lvls[-1]
        pattern = _guess_pattern(vals)
        if pattern:
            schema['pattern'] = pattern
    return schema


def _all_match(vals: list[str], *args: str):
    if len(vals) == 0:
        return False
    if len(args) == 0:
        return False
    for r in args:
        r = re.compile(r"^" + r + r"$")
        if all(map(r.match, vals)):
            return r.pattern


def _guess_pattern(vals: list[str], find_prefix_sufix=True):
    r = _all_match(
        vals,
        r"tt\d+",
        r'\d{4}-\d{2}-\d{2}',
        r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}',
        r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}',
        r"\d{2}-\d{2}-\d{4} \d{2}:\d{2}:[0-9\.]+",
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:[0-9\.]+",
    )
    if r:
        return r
    if find_prefix_sufix:
        prefix = ""
        suffix = ""
        for tp in zip(*vals):
            if len(set(tp)) > 1:
                break
            prefix = prefix + tp[0]
        for tp in zip(*["".join(reversed(v)) for v in vals]):
            if len(set(tp)) > 1:
                break
            suffix = tp[0] + suffix
        if prefix or suffix:
            new_vals = [v[len(prefix):len(v)-len(suffix)] for v in vals]
            if '' not in new_vals:
                pt = _guess_pattern(new_vals, find_prefix_sufix=False) or r"^.+$"
                return r"^" + re.escape(prefix) + pt[1:-1] + re.escape(suffix) + r"$"
    r = _all_match(
        vals,
        r'\d+',
        r'[a-z]',
        r'[A-Z]',
        r'[a-z0-9]',
        r'[A-Z0-9]',
        r'[a-zA-Z]',
        r'[a-zA-Z0-9]',
        r"https?://\S+"
    )
    if r:
        return r
    letters: set[str] = set()
    for i in vals:
        letters = letters.union(list(i))
    if letters and len(letters) < 20:
        re_letters = "".join(map(re.escape, sorted(letters)))
        return r'^['+re_letters+r']+$'
    r = _all_match(
        vals,
        r'\S+'
    )
    if r:
        return r


def read(file: str) -> list:
    with open(file) as f:
        js = json.load(f)
        if isinstance(js, list):
            return js
        return [js]


def get_schema(obj):
    builder = SchemaBuilder()
    if not isinstance(obj, (list, tuple)):
        obj = [obj]
    for o in obj:
        builder.add_object(o)
    schema = builder.to_schema()
    _complete_schema(schema, obj)
    return schema


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Crea un esquema json en base a varios json'
    )
    parser.add_argument(
        '--out',
        type=str,
        help='Fichero de salida',
        required=True
    )
    parser.add_argument(
        'files',
        type=str,
        help='Fichero con los json',
        nargs='+'
    )

    arr = []
    pargs = parser.parse_args()
    for f in pargs.files:
        arr.extend(read(f))
    schema = get_schema(arr)
    with open(pargs.out, "w") as f:
        json.dump(schema, f, indent=2)
