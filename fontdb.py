import sys
import os
import pickle
import hashlib
from rle import dec

def read20(fpath):
    ret = []
    with open(fpath, "rt", encoding='utf-8') as f:
        data = f.read()
    for c in data:
        if c in ["\r", "\n"]:
            continue
        ret.append(c)
    return ret

def update(db, bin, txt, szf):
    if os.path.exists(db):
        with open(db, "rb") as f:
            m = pickle.load(f)
    else:
        m = {}

    binarr = []
    with open(bin, "rb") as f:
        while True:
            data = f.read(8*16)
            if not data:
                break
            assert len(data) == 8*16

            binarr.append(data)

    txtarr = read20(txt)
     # 注意存了 0 大小
    szarr = [int(x,16) for x in read20(szf)]

    assert len(txtarr) == len(binarr)
    for i, c in enumerate(txtarr):
        if c in m:
            _, osz = m[c]
            if osz != 0 and szarr[i] == 0:
                # 不替换 0 宽度
                continue
            # if obin != binarr[i] or osz != szarr[i]:
            #     print('diffrent', c)
            #     continue
        szx = szarr[i]
        if c == '￥'and szx == 0:
           szx = 11
        m[c] = (binarr[i], szx)
        m[hashlib.md5(binarr[i]).hexdigest()] = c

    with open(db, "wb") as f:
        pickle.dump(m, f)

def addpal(db, bin):
    with open(db, "rb") as f:
        m = pickle.load(f)

    with open(bin, "rb") as f:
        f.seek(0x800)
        data = f.read(256*2)
    pal, _ = dec(data)
    assert len(pal) == 512
    m["PAL"] = pal

    with open(db, "wb") as f:
        pickle.dump(m, f)

def guess(db, bin, txt):
    with open(db, "rb") as f:
        m = pickle.load(f)

    with open(bin, "rb") as f:
        with open(txt, "wt", encoding='utf-8') as w:
            i = 0
            while True:
                data = f.read(8*16)
                if not data:
                    break

                if i > 0 and i % 20 == 0:
                    w.write("\n")
                md5 = hashlib.md5(data).hexdigest()
                if md5 in m:
                    w.write(m[md5])
                else:
                    w.write('□')
                i += 1

def check(db, bin, txt):
    with open(db, "rb") as f:
        m = pickle.load(f)

    binarr = []
    with open(bin, "rb") as f:
        while True:
            data = f.read(8*16)
            if not data:
                break
            assert len(data) == 8*16

            binarr.append(data)

    txtarr = read20(txt)

    for i, data in enumerate(binarr):
        md5 = hashlib.md5(data).hexdigest()
        if md5 in m:
            c = m[md5][0]
            if c != txtarr[i]:
                print(c, txtarr[i])

def main(argv):
    db = os.path.join(os.path.dirname(argv[2]), 'font.db')
    bin, txt, szf = argv[2]+".bin", argv[2]+".txt", argv[2]+".sz"

    if argv[1] == 'update':
        update(db, bin, txt, szf)
    elif argv[1] == 'pal':
        addpal(db, argv[2])
    elif argv[1] == 'guess':
        guess(db, bin, txt)
    elif argv[1] == 'check':
        check(db, bin, txt)

if __name__ == '__main__':
    main(sys.argv)
