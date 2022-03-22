from copyreg import pickle
from ini import Ini
from fontlib import FontLib
from merge import mark
import os
import pickle
from fontdb import read20
import io
from rle import (enc, dec)
import json
from linkdec import asm
import struct

def mkfont(db, ftbl, fcnt, lib: FontLib, fbin, maxsz):
	cs = read20(ftbl)

	# 先准备 bin
	bin = io.BytesIO()
	bin.write(enc(db['PAL']))

	mpos = {}
	for c in cs:
		b, sz = db[c]
		assert sz > 0, c
		mpos[c] = (bin.tell(), sz)
		bin.write(enc(b))

	assert bin.tell() <= maxsz, bin.tell()

	with open(fbin, "wb") as f:
		f.write(bin.getvalue())

	# idx -> off, sz, 字
	lst = []
	# 字体反查
	rmap = {}

	mm = {}
	mmr = set()
	for i in range(fcnt):
		c = lib.get(i)
		if c in mark:
			mm[i] = c
			mmr.add(c)

	i = 0
	di = 0
	while di < len(cs):
		c = None
		if i in mm:
			c = mm[i]
		else:
			while di < len(cs):
				tc = cs[di]
				di += 1
				if tc not in mmr:
					c = tc
					break
		assert c is not None

		lst.append(mpos[c])
		rmap[c] = i
		i += 1

	assert i == len(cs)

	return lst, rmap

def mklink(lst, rmap, flink, dstlinks, linksep, linkcnt):
	with open(flink, "rt", encoding='utf-8') as f:
		link = json.load(f)
	assert len(link) == linkcnt

	bins = [io.BytesIO(), io.BytesIO()]
	# code, secid, pp, func
	lst = []

	for v in link:
		secid, codeH, codeL, func, _ = v[0]
		if isinstance(func, str):
			func = int(func, 16)
		pp = 0xFFFFFFFF
		if len(v) > 1:
			dataid = 0
			if linksep is not None and secid >= linksep:
				dataid = 1
			bin = bins[dataid]
			pp = bin.tell()

			tmp = io.BytesIO()
			asm(rmap, tmp, v[1:])

			encb = enc(tmp.getvalue())
			assert dec(encb)[0] == tmp.getvalue()
			bin.write(encb)

		lst.append(((codeH<<4)|codeL, secid, pp, func))

	for i, dst in enumerate(dstlinks):
		with open(dst, "wb") as f:
			f.write(bins[i].getvalue())
	return lst

def patchexe(flst, llst, ini: Ini):
	# 写码表
	with open(ini.dstexe, "rb+") as f:
		f.seek(ini.fonttbl - ini.base)

		for off, sz in flst:
			assert off <= 0xffffff
			# f.write(struct.pack("<2I", ini.fontbuf+off, sz))
			# 采用压缩法
			f.write(struct.pack("<I", (off << 8) | sz))

		f.seek(ini.linktbl - ini.base)

		for code, secid, pp, func in llst:
			if pp != 0xFFFFFFFF:
				pp += ini.linkbuf
			f.write(struct.pack("<2BH2I", code, secid, 0, pp, func))

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
	flst, rmap = mkfont(db, ftbl, ini.fontcnt, lib, fbin, ini.fontmax)
	print(len(flst), hex(len(flst)*8), len(flst)<=ini.fontcnt)
	assert len(flst) > ini.fontcnt and len(flst) <= ini.fontcnt * 2

	llst = mklink(flst, rmap, flink, dstlinks, ini.linkid()[1], ini.linkcnt)
	if os.path.exists(ini.dstexe):
		patchexe(flst, llst, ini)
