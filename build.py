from copyreg import pickle
from ini import Ini
from fontlib import FontLib
from merge import mark
import os
import pickle
from fontdb import read20
import io
from rle import enc
import json
from linkdec import asm

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
		assert sz > 0, c
		lst.append((bin.tell(), sz, c))
		rmap[c] = i
		bin.write(enc(b))
		i += 1

	with open(fbin, "wb") as f:
		f.write(bin.getvalue())
	return lst, rmap

def mklink(lst, rmap, flink, dstlinks, linksep, linkcnt):
	with open(flink, "rt", encoding='utf-8') as f:
		link = json.load(f)
	assert len(link) == linkcnt

	bins = [io.BytesIO(), io.BytesIO()]
	# code, secid, pp, func
	lst = []

	for v in link:
		secid, codeH, codeL, func = v[0]
		pp = 0xFFFFFFFF
		if len(v) > 1:
			dataid = 0
			if linksep is not None and secid >= linksep:
				dataid = 1
			bin = bins[dataid]
			pp = bin.tell()

			tmp = io.BytesIO()
			asm(rmap, tmp, v[1:])
			bin.write(enc(tmp.getvalue()))

			lst.append(((codeH<<4)|codeL, secid, pp, func))

	for i, dst in enumerate(dstlinks):
		with open(dst, "wb") as f:
			f.write(bins[i].getvalue())
	return lst

def build(ini: Ini, lib: FontLib):
	fontdb = os.path.join(os.path.dirname(ini.font), 'font.db')
	with open(fontdb, "rb") as f:
		db = pickle.load(f)

	fontname = "{}.{}".format(ini.font, ini.fontid)
	ftbl = fontname + ".cn.txt"
	fbin = "{}.{}.bin".format(ini.dstfont, ini.fontid)

	linkname = "{}.{}".format(ini.link, ini.linkid()[0][0])
	flink = linkname + ".cn.txt"
	dstlinks = ["{}.{}.bin".format(ini.dstlink, id) for id in ini.linkid()[0]]

	# 生成 字库 lst bin sz
	flst, rmap = mkfont(db, ftbl, ini.fontcnt, lib, fbin)
	llst = mklink(flst, rmap, flink, dstlinks, ini.linkid()[1], ini.linkcnt)
