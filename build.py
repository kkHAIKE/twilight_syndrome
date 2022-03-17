from copyreg import pickle
from ini import Ini
from fontlib import FontLib
from merge import mark
import os
import pickle
from fontdb import read20
import io
from rle import enc

def mkfont(db, ftbl, fcnt, lib: FontLib, fbin):
	cs = read20(ftbl)

	bin = io.BytesIO()
	bin.write(enc(db['PAL']))

	# idx -> off, sz, 字
	lst = []
	# 字体反查
	rmap = {}

	i = 0
	di = 0
	while di < len(cs):
		c = None
		if i < fcnt:
			c = lib.get(i)
			if c not in mark:
				c = None
		if c is None:
			c = cs[di]
			di += 1

		b, sz = db[c]
		lst.append((bin.tell(), sz, c))
		rmap[c] = i
		bin.write(enc(b))
		i += 1

	with open(fbin, "wb") as f:
		f.write(bin.getvalue())
	return lst, rmap

def build(ini: Ini, lib: FontLib):
	# 生成 字库 lst bin sz
	fontdb = os.path.join(os.path.dirname(ini.font), 'font.db')
	with open(fontdb, "rb") as f:
		db = pickle.load(f)

	fontname = "{}.{}".format(ini.font, ini.fontid)
	ftbl = fontname + ".cn.txt"
	dstfont = "{}.{}".format(ini.dstfont, ini.fontid)
	fbin = dstfont + ".bin"
	mkfont(db, ftbl, ini.fontcnt, lib, fbin)
