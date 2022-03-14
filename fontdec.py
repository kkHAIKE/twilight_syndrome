from ini import Ini
from rle import dec
from cdb import CDB
import struct
import pickle
from PIL import Image

def tob(x):
    return int((x &0x1f) * 0xff/0x1f)

def makepal(d: bytes):
    ret = bytearray(b'RIFF\x10\x04\x00\x00PAL data\x04\x04\x00\x00\x00\x03\x00\x01')
    n = len(d)//2
    for v in struct.unpack("<{}H".format(n), d):
        r, g, b = tob(v), tob(v >> 5), tob(v >> 10)
        a = 255
        if r == 0 and g == 0 and b == 0:
            # black 特别情况
            a = 0
        if ((v >> 15) &1) == 1:
            a = 160

        ret.extend([r, g, b, a])
    # 补齐 256
    # if n < 256:
    #     for _ in range(256 - n):
    #         ret.extend([0, 0, 0, 0])

    return ret

def makepng(fpath, pal, bin):
    sz = len(bin) // (16*8)
    hn = (sz +19)//20
    img = Image.new('P', (20 * 16, hn * 16))
    img.putpalette(pal[24:], 'RGBA')

    i = 0
    for yi in range(hn):
        for xi in range(20):
            if i == sz:
                # 补最后的透明
                for yy in range(16):
                    for xx in range(16):
                        img.putpixel((xi*16 + xx, yi*16 + yy), 4)
                continue

            tmp = bin[i *(16*8): (i+1) *(16*8)]
            for yy in range(16):
                for xx in range(8):
                    c = tmp[yy*8 + xx]
                    l = c & 0xf
                    h = c >> 4
                    img.putpixel((xi*16 + xx*2, yi*16 + yy), l)
                    img.putpixel((xi*16 + xx*2 +1, yi*16 + yy), h)

            i += 1
    img.save(fpath, 'png')

def _fontdec(fpath, idx):
    db = CDB(fpath)
    data = db.read(idx)

    first = False
    binout = bytearray()
    olen = len(data)
    sp = 0
    l = []
    pal = None

    while True:
        dst, data = dec(data)

        if not dst or not any(dst):
            break

        if not first:
            first = True
            pal = makepal(dst)
        else:
            l.append((sp, len(binout)))
            binout.extend(dst)
        sp = olen - len(data)

    fname = "{}.{}".format(fpath, idx)

    with open(fname + ".bin", "wb") as o:
        o.write(binout)
    with open(fname + ".lst", "wb") as o:
        pickle.dump(l, o, pickle.DEFAULT_PROTOCOL)
    with open(fname + ".pal", "wb") as o:
        o.write(pal)
    makepng(fname + ".png", pal, binout)

# xxx = '..\\file0\\DAT\\FONT\\KFONT.CDB'
# for v in [0, 3, 1, 5, 2, 7]:
#     _fontdec(xxx, v)

def fontdec(ini: Ini):
    _fontdec(ini.font, ini.fontid)