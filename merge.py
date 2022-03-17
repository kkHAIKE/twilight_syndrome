import io
from ini import Ini
import re
import os
import json

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
        # if i in [55]:
        #     continue
        assert ctrlRe.findall(s) == ctrlRe.findall(dst[i]), i
    arr = list(ss)
    arr.sort()
    return arr, dst

mark = '▷▽◲⍽◎0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz' + \
    'ー。、！？”$%&’￥=:⋯·.‘()―「」『』~‥♥；'

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
        assert n2 > 0 and n2 < 4, "{},{},{},{}".format(n, n2, di, line)
        if n != n2:
            line = line[:m.start(1)] + str(n2) + line[m.end(1):]
    return line

def mergeLink(src, dst, lines):
    with open(src, "rt", encoding='utf-8') as f:
        data = json.load(f)

    di = 0
    for v in data:
        for vv in v:
            if vv[0] == "TEXT":
                line = lines[di].rstrip("\r\n")
                line = headfix(line, di)

                vv[1] = line
                di += 1
    assert di == len(lines)

    with open(dst, "wt", encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

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
