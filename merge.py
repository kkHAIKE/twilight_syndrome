from io import TextIOWrapper
from ini import Ini
import re

def readline(f: TextIOWrapper):
    arr = []
    while True:
        line = f.readline()
        if not line:
            break
        line = line.rstrip('\r\n')

        arr.append(line)
    return arr

def checkRawGetAllChar(fsrc, fdst):
    with open(fsrc, "rt", encoding='utf-8') as f:
        src = f.readlines()
    with open(fdst, "rt", encoding='utf-8') as f:
        dst = f.readlines()
    assert len(src) == len(dst)

    ctrlRe = re.compile(r'<[^>]+>')
    ss = set()
    for i, s in enumerate(src):
        raw = ctrlRe.sub('', dst[i])
        raw = raw.rstrip('\r\n')
        for c in raw:
            ss.add(c)

        if s == dst[i]:
            continue

        assert ctrlRe.findall(s) == ctrlRe.findall(dst[i])
    arr = list(ss)
    arr.sort()
    return arr

# 合并 raw 和 cn 文件到脚本
# 并且自动检查错误，和替换 HEAD
def merge(ini: Ini):
    name = "{}.{}".format(ini.link, ini.linkid()[0][0])
    fsrc = name + ".raw.txt"
    fdst = name + ".cn.raw.txt"
    cs = checkRawGetAllChar(fsrc, fdst)

    print(cs)
