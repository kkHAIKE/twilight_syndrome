from cdb import CDB
from rle import dec
import os
import struct
from PIL import Image
from fontdec import makepal

ALLLINK_CDB = '/Users/dexter/Downloads/ps1/file0/DAT/SINKOU/ALLLINK.CDB'

def dump():
    db = CDB(ALLLINK_CDB)
    data = db.read(0)
    db = None

    arr = [
        [0, 5950, 12900],
        [18640, 23442, 30015],
        [34474, 39916, 45471],
        [72106, 75244, 81126],
        [50578, 58041, 64927],
        [233481, 238416, 242566],
        [104221, 110186, 115832],
        [138755, 142122, 147050],
        [184395, 187424, 192913],
        [217529, 222088, 227333],
        [120416, 125066, 131955],
        [151845, 157923, 164825],
        [196968, 203915, 210903],
        [171682, 174557, 180292],
        [88166, 93779, 99112],
    ]

    arr2 = [
        248698,
        252336,
        262307,
        272164,
        289959,
        292380,
        298425,
        307280,
        322767,
        324514,
        329285,
        338321,
        350909,
        351926,
        357088,
        364196,
        375195,
        379750,
        387873,
        397228,
        416117,
        422949,
        432111,
        443705,
        283195,
        316421,
        347187,
        370841,
        407596,
        455659,
        289050,
        321465,
        349792,
        374239,
        414592,
        463344,
        467690,
        464134,
        471588,
    ]

    dpath = os.path.join(os.path.dirname(ALLLINK_CDB), 'ALLLINK', 'ALLLINK')

    for i, v in enumerate(arr):
        for j, vv in enumerate(v):
            tmp, _ = dec(data[vv:])
            with open(f'{dpath}.{i}.{j}.tim', "wb") as f:
                f.write(tmp)

    for i, v in enumerate(arr2):
        tmp, _ = dec(data[v:])
        with open(f'{dpath}.{i+len(arr)}.tim', "wb") as f:
            f.write(tmp)

def tim2png(fpath):
    with open(fpath, "rb") as f:
        id1, id2, clutSz, orgX, orgY, clrs, clutN = struct.unpack(
            "<3I4H", f.read(20),
        )

        assert id1 == 0x10 and id2 == 8 and clrs == 16
        print(orgX, orgY)
        # assert orgX == 0 and orgY == 0
        assert clrs * clutN * 2 + 12 == clutSz
        # npal = clrs * clutN
        pal = makepal(f.read(clutSz - 12))

        imgSz, iorgX, iorgY, w, h = struct.unpack(
            "<I4H", f.read(12),
        )
        # print(iorgX, iorgY)
        assert iorgX == 0 and iorgY == 0
        assert w * h * 2 + 12 == imgSz, w * h * 2 + 12

        img = Image.new('P', (w * 4, h))
        img.putpalette(pal[24:], 'RGBA')

        for y in range(h):
            for x in range(w*2):
                b = f.read(1)[0]
                img.putpixel((x*2, y), b & 0xf)
                img.putpixel((x*2+1, y), b >> 4)

        dstpath = os.path.splitext(fpath)[0] + ".png"
        img.save(dstpath, "png")

for i in range(6):
    tim2png(f'/Users/dexter/Downloads/ps1/file0/DAT/SINKOU/ALLLINK/ALLLINK.{45+i}.tim')
