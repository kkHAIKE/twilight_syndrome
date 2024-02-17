import io
from ini import Ini
import re
import os
import json
import ctypes

def readline(f: io.TextIOWrapper):
    arr = []
    while True:
        line = f.readline()
        if not line:
            break
        line = line.rstrip('\r\n')

        arr.append(line)
    return arr

def checkRawAndGet(fsrc, fdst):
    with open(fsrc, "rt", encoding='utf-8') as f:
        src = f.readlines()
    with open(fdst, "rt", encoding='utf-8') as f:
        dst = f.readlines()
    assert len(src) == len(dst)

    ctrlRe = re.compile(r'(<[^>]+>)|⍽')
    ss = set()
    for i, s in enumerate(src):
        raw = ctrlRe.sub('', dst[i])
        raw = raw.rstrip('\r\n')
        for c in raw:
            ss.add(c)

        if s == dst[i]:
            continue

        # print(ctrlRe.findall(s), ",", ctrlRe.findall(dst[i]))
        # if i in [55, 363]:
        #     continue
        assert ctrlRe.findall(s) == ctrlRe.findall(dst[i]), i
    arr = list(ss)
    arr.sort()
    return arr, dst

mark = '▷▽◲⍽◎0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' + \
    '‒ー。、！？”$%&’￥=:⋯·.‘()―「」『』~‥♥；〇♪，◯゛・↑←'

noneed = ''

def makeTbl(src, dst, cs, need):
    cs2 = []
    for c in cs:
        if c not in mark:
            cs2.append(c)

    ss = set(cs2)
    if os.path.exists(need):
        with open(need, "rt", encoding='utf-8-sig') as f:
            ss |= set(f.read().rstrip("\r\n"))

    ssa = list(ss)
    ssa.sort()
    with open(need, "wt", encoding='utf-8-sig') as f:
        for c in ssa:
            f.write(c)

    di = 0
    n = 0
    with open(src, "rt", encoding='utf-8') as f:
        data = f.read()

    with open(dst, "wt", encoding='utf-8') as f:
        for c in data:
            if c in ["\r", "\n"]:
                continue

            if n > 0 and n % 20 == 0:
                f.write("\n")
            if c in mark:
                f.write(c)
            elif di < len(cs2):
                f.write(cs2[di])
                di += 1
            else:
                f.write(c)
            n += 1

        while di < len(cs2):
            if n > 0 and n % 20 == 0:
                f.write("\n")
            f.write(cs2[di])
            di += 1
            n += 1

def headfix(line, di):
    headRe = re.compile(r'<HEAD,(\d)>')
    for m in headRe.finditer(line):
        n = int(m.group(1))
        idx = line.index(':', m.end(0))
        n2 = idx - m.end(0)
        # ユカリ·チサト
        assert n2 > 0 and n2 <= 7, "{},{},{},{}".format(n, n2, di, line)
        if n != n2:
            line = line[:m.start(1)] + str(n2) + line[m.end(1):]
    return line

class NoIndent(object):
    """ Value wrapper. """
    def __init__(self, value):
        self.value = value

class MyEncoder(json.JSONEncoder):
    FORMAT_SPEC = '@@{}@@'
    regex = re.compile(FORMAT_SPEC.format(r'(\d+)'))

    def __init__(self, **kwargs):
        # Save copy of any keyword argument values needed for use here.
        self.__sort_keys = kwargs.get('sort_keys', None)
        super(MyEncoder, self).__init__(**kwargs)

    def default(self, obj):
        return (self.FORMAT_SPEC.format(id(obj)) if isinstance(obj, NoIndent)
                else super(MyEncoder, self).default(obj))

    def encode(self, obj):
        format_spec = self.FORMAT_SPEC  # Local var to expedite access.
        json_repr = super(MyEncoder, self).encode(obj)  # Default JSON.

        # Replace any marked-up object ids in the JSON repr with the
        # value returned from the json.dumps() of the corresponding
        # wrapped Python object.
        for match in self.regex.finditer(json_repr):
            # see https://stackoverflow.com/a/15012814/355230
            id = int(match.group(1))
            no_indent = ctypes.cast(id, ctypes.py_object).value
            json_obj_repr = json.dumps(no_indent.value,
                sort_keys=self.__sort_keys,
                ensure_ascii=False,
            )

            # Replace the matched id string with json formatted representation
            # of the corresponding Python object.
            json_repr = json_repr.replace(
                            '"{}"'.format(format_spec.format(id)), json_obj_repr)

        return json_repr

def mergeLink(src, dst, lines):
    with open(src, "rt", encoding='utf-8') as f:
        data = json.load(f)

    di = 0
    for v in data:
        for i, vv in enumerate(v):
            if vv[0] == "TEXT":
                line = lines[di].rstrip("\r\n")
                line = headfix(line, di)

                vv[1] = line
                di += 1
            # 缩进修正
            v[i] = NoIndent(vv)
    assert di == len(lines)

    js = json.dumps(data, cls=MyEncoder, indent=2, ensure_ascii=False)
    with open(dst, "wt", encoding='utf-8') as f:
        f.write(js)

# 合并 raw 和 cn 文件到脚本
# 并且自动检查错误，和替换 HEAD
def merge(ini: Ini):
    linkname = "{}.{}".format(ini.link, ini.linkid()[0][0])
    flink = linkname + ".txt"
    flinkcn = linkname + ".cn.txt"
    fraw = linkname + ".raw.txt"
    frawcn = linkname + ".cn.raw.txt"
    fontname = "{}.{}".format(ini.font, ini.fontid)
    ftbl = fontname + ".txt"
    ftblcn = fontname + ".cn.txt"
    need = ini.font + ".need.txt"

    cs, lines = checkRawAndGet(fraw, frawcn)
    makeTbl(ftbl, ftblcn, cs, need)
    mergeLink(flink, flinkcn, lines)
