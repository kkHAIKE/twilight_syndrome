from cdb import CDB
import struct
from rle import dec
import io
import json
from fontlib import FontLib
from ini import Ini
import binascii

def mkcode(cmd0, cmd1, cmd2=0):
    return struct.pack('<H', (cmd0<<14) | (cmd1<<8) | cmd2)

def asmtxt(rmap, bin: io.BytesIO, txt: str):
    sm = {
        'BEGIN': 9,
        'SPD': 3,
        'WAIT': 4,
        'RET': 1,
        'PRESS': 5,
        'NEXT': 6,
        'END': 0xa,
        'HEAD': 0xd,
        'SEL': 0x17,
        'COL': 2,
        'CASE': 0x18,
        'CEND': 0x28,
        'x8B': 0xb,
        'WAIT1': 0xf,
    }

    i = 0
    while i < len(txt):
        c = txt[i]
        if c == '<':
            idx = txt.index('>', i)
            arr = txt[i+1: idx].split(',')
            i = idx + 1

            if arr[0] in sm:
                cmd2 = 0
                if len(arr) > 1:
                    cmd2 = int(arr[1])
                bin.write(mkcode(2, sm[arr[0]], cmd2))
            else:
                assert False
        else:
            bin.write(struct.pack("<H", rmap[c]))
            i += 1

def asm(rmap, bin: io.BytesIO, para):
    sm = {
        'RUN': 0xf,
        'FINGO': 0xc,
        'SEC': 0x15,
        'xCA': 0xa,
        'FLG': 0x14,
        'BEAT+': 4,
        'WAIT': 6,
        'BEAT-': 2,
        'BEAT++': 5,
        'xC3': 3,
        'xC9': 9,
    }

    for v in para:
        if v[0] == 'FIRST':
            bin.write(struct.pack("<H", v[1]))
        elif v[0] == 'TEXT':
            asmtxt(rmap, bin, v[1])
        elif v[0] == 'FIN':
            bin.write(b'\xff\xff')
            for vv in v[1:]:
                bin.write(struct.pack("<H", vv))
        elif v[0] in sm:
            cmd2 = 0
            if len(v) > 1:
                cmd2 = v[1]
            bin.write(mkcode(3, sm[v[0]], cmd2))
        elif v[0] == 'XA':
            bin.write(mkcode(3, 8, v[1]))
            bin.write(struct.pack("<H", v[2]))
        elif v[0] == 'AWAIT':
            assert v[1] in [0, 2, 1, 3, 4]
            bin.write(mkcode(3, 0xe, v[1]))
            if v[1] in [1, 3, 4]:
                bin.write(struct.pack("<H", v[2]))
        elif v[0] == 'ACT0':
            bin.write(mkcode(3, 0x10+v[1], 0))
            bin.write(struct.pack("<H", v[2]))
        elif v[0] == 'ACT1':
            bin.write(mkcode(3, 0x16+v[1], v[2]))
            if v[2] < 2:
                bin.write(struct.pack("<H", v[3]))
        else:
            assert False


def dism(para: list, lines: list, asm: bytes, lib: FontLib):
    fc, = struct.unpack("<H", asm[:2])
    para.append(['FIRST', fc])

    # print(binascii.b2a_hex(asm))
    # patch
    if asm == binascii.a2b_hex('010000ca0089038d530034005600fb0050019d0013003f0039004200f200008100854e0034002d00a50202001300020008002c00090016001a00fd00fd00fd000086008a11c87f00100034005c006f00ccc402ce00cf00d402ceffff'):
        asm = binascii.a2b_hex('010000ca0089038d530034005600fb0050019d0013003f0039004200f200008100854e0034002d00a50202001300020008002c00090016001a00fd00fd00fd00008611c87f00100034005c006f00008accc402ce00cf00d402ceffff')
        #[[10, 13, 1, '0x8005ba0c', 'I155'], ['FIRST', 1], ['xCA'], ['TEXT', '<BEGIN><HEAD,3>ユカリ:待ってチサト！<RET><PRESS,0>ミカを置いていくわけには···<NEXT>'], ['XA', 17, 127], ['TEXT', 'たカンジ<END>'], ['BEAT+', 204], ['AWAIT', 2], ['RUN', 0], ['FLG'], ['AWAIT', 2], ['FIN']]
    elif asm == binascii.a2b_hex('020003cf00d40089028d4e003400fb00fd00fd00fd00b70204001000f3000086029700c302cfffff'):
        asm = binascii.a2b_hex('020003cf00d40089028d4e003400fb00fd00fd00fd00b70204001000f300008600c302cfffff')
        # [[3, 13, 1, 0, 'I208'], ['FIRST', 2], ['RUN', 3], ['FLG'], ['TEXT', '<BEGIN><HEAD,2>ミカ:···消えた？<NEXT>'], ['xC3'], ['RUN', 2], ['FIN']]

    i = 2
    final = False
    txt = io.StringIO()
    final_CC = False
    final_97 = 0
    final_8b = False
    intxt = False

    while i < len(asm):
        assert not final
        # if final:
        #     para.append(['FINALOUT', *struct.unpack("<{}H".format((len(asm)-i)//2), asm[i:])])
        #     break

        code, = struct.unpack("<H", asm[i:i+2])
        i += 2

        cmd0 = code >> 14
        cmd1 = (code >> 8) & 0x3f
        cmd2 = code &0xff

        if (code == 0xFFFF or cmd0 == 3) and txt.tell() > 0:
            para.append(['TEXT', txt.getvalue()])
            lines.append(txt.getvalue()+"\n")
            txt = io.StringIO()

        if code == 0xFFFF:
            final = True
            vv = ['FIN']
            if final_97:
                vv.extend(struct.unpack("<{}H".format(final_97), asm[i:i + final_97 *2]))
                i += final_97 *2
            if final_CC or final_8b:
                v, = struct.unpack("<H", asm[i:i+2])
                i += 2
                vv.append(v)
            para.append(vv)
        elif cmd0 == 2:
            # 8
            if cmd1 == 9:
                txt.write("<BEGIN>")
                intxt = True
            elif cmd1 == 3:
                txt.write("<SPD,{}>".format(cmd2))
            elif cmd1 == 4:
                txt.write("<WAIT,{}>".format(cmd2))
            elif cmd1 == 1:
                txt.write("<RET>")
            elif cmd1 == 5:
                txt.write("<PRESS,{}>".format(cmd2))
            elif cmd1 == 6:
                txt.write("<NEXT>")
            elif cmd1 == 0xa:
                txt.write("<END>")
                intxt = False
            elif cmd1 == 0xd:
                txt.write("<HEAD,{}>".format(cmd2))
            elif cmd1 == 0x17: # a7
                final_97 = cmd2
                txt.write("<SEL,{}>".format(cmd2))
            elif cmd1 == 2:
                txt.write("<COL,{}>".format(cmd2))
            elif cmd1 == 0x18:
                txt.write("<CASE,{}>".format(cmd2))
            elif cmd1 == 0x28:
                txt.write("<CEND,{}>".format(cmd2))
            elif cmd1 == 0xb:
                final_8b = True
                txt.write("<x8B,{}>".format(cmd2))
            elif cmd1 == 0xf:
                txt.write("<WAIT1>")
            else:
                assert False, hex(code)
        elif cmd0 == 3:
            # C
            if cmd1 == 0xf:
                para.append(['RUN', cmd2])
            elif cmd1 == 8:
                v, = struct.unpack("<H", asm[i:i+2])
                i += 2
                para.append(['XA', cmd2, v])
            elif cmd1 == 0xc:
                final_CC = True
                para.append(['FINGO'])
            elif cmd1 == 0xe:
                if cmd2 in [0, 2]:
                    para.append(['AWAIT', cmd2])
                elif cmd2 in [1, 3, 4]:
                    v, = struct.unpack("<H", asm[i:i+2])
                    i += 2
                    para.append(['AWAIT', cmd2, v])
                else:
                    assert False, hex(code) + hex(cmd2)
            elif cmd1 == 0x15:
                para.append(['SEC', cmd2])
            elif cmd1 == 0xa:
                para.append(['xCA'])
            elif cmd1 == 0x14:
                para.append(['FLG'])
            elif cmd1 in [0x10, 0x11, 0x12]:
                v, = struct.unpack("<H", asm[i:i+2])
                i += 2
                para.append(['ACT0', cmd1 -0x10, v])
            elif cmd1 in [0x16, 0x17, 0x18]:
                vv = ['ACT1', cmd1 -0x16, cmd2]
                if cmd2 < 2:
                    v, = struct.unpack("<H", asm[i:i+2])
                    i += 2
                    vv.append(v)
                para.append(vv)
            elif cmd1 == 4:
                para.append(['BEAT+', cmd2])
            elif cmd1 == 6:
                para.append(['WAIT', cmd2])
            elif cmd1 == 2:
                para.append(['BEAT-', cmd2])
            elif cmd1 == 5:
                para.append(['BEAT++', cmd2])
            elif cmd1 == 3:
                para.append(['xC3'])
            elif cmd1 == 9:
                para.append(['xC9'])
            elif cmd1 == 1:
                v, = struct.unpack("<H", asm[i:i+2])
                i += 2
                para.append(['xC1', v])
            elif cmd1 == 0xd:
                v, = struct.unpack("<H", asm[i:i+2])
                i += 2
                para.append(['xCD', v])
            else:
                assert False, hex(code)

        elif cmd0 == 0:
            assert intxt, "{},{}".format(i, hex(code))
            txt.write(lib.get(code))# &0xfff))
        else:
            assert False


def linkdec(ini: Ini, lib: FontLib):
    linkdb = CDB(ini.link)
    linkids, linksep = ini.linkid()
    linkdatas = [linkdb.read(idx) for idx in linkids]
    linkdb = None

    cap = []
    lines = []
    with open(ini.exe, 'rb') as f:
        tblp = ini.linktbl - ini.base
        f.seek(tblp)

        ss = set()

        for i in range(ini.linkcnt):
            code, secid, ignore, pp, func = struct.unpack('<2BH2I', f.read(12))
            assert ignore == 0
            if func != 0:
                func = hex(func)
            para = [[secid, code>>4, code&0xf, func, f'I{i+10}']]

            dataid = 0
            if linksep is not None and secid >= linksep:
                dataid = 1

            if pp != 0xFFFFFFFF:
                assert (pp, dataid) not in ss, i
                ss.add((pp, dataid))

                dst, _ = dec(linkdatas[dataid][pp - ini.linkbuf:])
                # try:
                dism(para, lines, dst, lib)
                # except:
                #     with open("{}.{}".format(ini.link, linkids[0]) + ".raw.txt", "wt", encoding='utf-8') as f:
                #         f.writelines(lines)
                #     exit(0)

            cap.append(para)

    name = "{}.{}".format(ini.link, linkids[0])
    with open(name + ".txt", "wt", encoding="utf-8") as f:
        json.dump(cap, f, indent=2, ensure_ascii=False)

    with open(name + ".raw.txt", "wt", encoding='utf-8') as f:
        f.writelines(lines)
