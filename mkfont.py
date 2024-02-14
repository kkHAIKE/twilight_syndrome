
import re
import os
from PIL import Image

class FontInfo:
    def __init__(self, m: re.Match):
        self.code, self.x, self.y, self.w, self.h, = int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4)), int(m.group(5))
        self.xo, self.yo, adv, page = int(m.group(6)), int(m.group(7)), int(m.group(8)), int(m.group(9))
        assert adv == 14 and page == 0

def readFnt(fpath):
    nameRe = re.compile(r'^page id=0 file="(.+?)"$')
    cntRe = re.compile(r'^chars count=(\d+)$')
    fontRe = re.compile(r'char id=(\d+)\s+x=(\d+)\s+y=(\d+)\s+width=(\d+)\s+height=(\d+)\s+xoffset=(-?\d+)\s+yoffset=(-?\d+)\s+xadvance=(\d+)\s+page=(\d+)\s+chnl=\d+$')

    arr = []
    name = None
    cnt = None
    with open(fpath, "rt") as f:
        while True:
            line = f.readline()
            if not line:
                break
            line = line.rstrip("\r\n")

            if name is None:
                m = nameRe.match(line)
                if m is not None:
                    name = m.group(1)
                continue

            if cnt is None:
                m = cntRe.match(line)
                if m is not None:
                    cnt = int(m.group(1))
                continue

            m = fontRe.match(line)
            if m is not None:
                arr.append(FontInfo(m))

    # print(name, cnt)
    assert len(arr) == cnt, len(arr)
    return name, arr

def onefont(img, c: FontInfo):
    lp = 0 # left pos
    flag = False
    for xi in range(c.w):
        for yi in range(c.h):
            clr = img.getpixel((c.x + xi, c.y + yi))
            if clr != (0, 0, 0, 0):
                lp = xi
                flag = True
                break
        if flag:
            break

    rp = 0 # right pos
    flag = False
    for xi in range(c.w-1, -1, -1):
        for yi in range(c.h):
            clr = img.getpixel((c.x + xi, c.y + yi))
            if clr != (0, 0, 0, 0):
                rp = c.w - xi - 1
                flag = True
                break
        if flag:
            break

    w = c.w - lp - rp
    assert w > 2 and w < 16

    yo = c.yo + 1
    sx, sy = c.x + lp, c.y
    h = c.h
    dy = 0
    if yo < 0:
        h += yo
        sy -= yo
    elif h < 16:
        dy = yo
    h = min(h, 16)
    assert h > 2

    bin = [0x44] * (8*16)
    for yy in range(h):
        for xx in range(w):
            clr = img.getpixel((sx + xx, sy + yy))
# (255, 255, 255, 255)
# (180, 180, 180, 160)
# (139, 139, 139, 160)
# (106, 106, 106, 160)
# (0, 0, 0, 0)
# (8, 8, 8, 160)
# (0, 0, 0, 160)
            if clr == (0, 0, 0, 0):
                code = 4
            elif clr == (255, 255, 255, 255):
                code = 0
            elif clr == (0, 0, 0, 255):
                code = 6
            else:
                assert False, clr

            if xx % 2 == 0:
                bin[(dy + yy)*8 + xx//2] &= 0xf0
                bin[(dy + yy)*8 + xx//2] |= code
            else:
                bin[(dy + yy)*8 + xx//2] &= 0xf
                bin[(dy + yy)*8 + xx//2] |= code << 4
    return chr(c.code), bin, w-1

def mkfont(fpath):
    name, arr = readFnt(fpath)
    pngpath = os.path.join(os.path.dirname(fpath), name)
    img = Image.open(pngpath)

    txtw = open('custom.txt', 'wt', encoding='utf-8')
    szw = open('custom.sz', 'wt')
    binw = open('custom.bin', 'wb')

    for i, c in enumerate(arr):
        if i > 0 and i % 20 == 0:
            txtw.write("\n")
            szw.write("\n")
        fc, fb, sz = onefont(img, c)
        txtw.write(fc)
        if sz < 10:
            szw.write(chr(ord('0') + sz))
        else:
            szw.write(chr(ord('A') + sz - 10))
        binw.write(bytearray(fb))

    txtw.close()
    szw.close()
    binw.close()

# mkfont(r'..\py\fnt3\Twilight Syndrome.fnt')
