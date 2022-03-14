import pickle
import struct
from ini import Ini

def readTbl1(fpath, addr, cnt):
    arr = []
    with open(fpath, "rb") as f:
        f.seek(addr)

        for _ in range(cnt):
            arr.append(struct.unpack("<2I", f.read(8)))
    return arr

def readTbl2(fpath):
    with open(fpath, "rt", encoding="utf-8") as f:
        lines = f.readlines()

    s = set()
    arr = []
    for i, line in enumerate(lines):
        line = line.rstrip("\r\n")
        # 每行20个
        if i != len(lines)-1:
            assert len(line) == 20, len(line)

        for c in line:
            assert c not in s, c
            s.add(c)

            arr.append(c)
    return arr

# readTbl("..\\file0\\DAT\\FONT\\KFONT.CDB.0.txt")

class FontLib:
    def __init__(self, ini: Ini):
        base = ini.fontbuf

        name = "{}.{}".format(ini.font, ini.fontid)
        with open(name + ".lst", "rb") as f:
            lst = pickle.load(f)
        self._m = {}
        self._mr = {}
        for k, v in lst:
            assert v % (8*16) == 0
            self._m[base + k] = v // (8*16)
            self._mr[v // (8*16)] = base + k

        self._tbl2 = readTbl2(name + ".txt")
        self._tbl1 = readTbl1(ini.exe, ini.fonttbl-ini.base, ini.fontcnt)

        self._tbl2r = {}
        for i, v in enumerate(self._tbl2):
            self._tbl2r[v] = i
        self._tbl1r = {}
        for i, v in enumerate(self._tbl1):
            assert v[0] not in self._tbl1r
            self._tbl1r[v[0]] = (i, v[1])

    def get(self, code):
        return self._tbl2[self._m[self._tbl1[code][0]]]

    def getr(self, c):
        return self._tbl1r[self._mr[self._tbl2r[c]]]

    def alllen(self):
        r = []
        for c in self._tbl2:
            l = 0
            try:
                l = self.getr(c)[1]
            except:
                pass
            r.append(l)
        return r

def dumpsz(ini: Ini, lib: FontLib):
    with open("{}.{}.sz".format(ini.font, ini.fontid), "wt") as f:
        arr = lib.alllen()

        for i, v in enumerate(arr):
            if i > 0 and i % 20 == 0:
                f.write("\n")
            if v < 10:
                f.write(str(v))
            else:
                f.write(chr(ord('A')+v-10))
