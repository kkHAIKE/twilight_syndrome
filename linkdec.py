from cdb import CDB
import struct
from rle import dec
import io
import json
from fontlib import FontLib
from ini import Ini

def dism(para: list, lines: list, asm: bytes, lib: FontLib):
    fc, = struct.unpack("<H", asm[:2])
    para.append(['FIRST', fc])

    # print(binascii.b2a_hex(asm))

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
                para.append(['xCF', cmd2])
            elif cmd1 == 8:
                v, = struct.unpack("<H", asm[i:i+2])
                i += 2
                para.append(['XA', cmd2, v])
            elif cmd1 == 0xc:
                final_CC = True
                para.append(['FINGO'])
            elif cmd1 == 0xe:
                if cmd2 in [0, 2]:
                    para.append(['xCE', cmd2])
                elif cmd2 in [1, 3, 4]:
                    v, = struct.unpack("<H", asm[i:i+2])
                    i += 2
                    para.append(['xCE', cmd2, v])
                else:
                    assert False, hex(code) + hex(cmd2)
            elif cmd1 == 0x15:
                para.append(['xD5', cmd2])
            elif cmd1 == 0xa:
                para.append(['xCA'])
            elif cmd1 == 0x14:
                para.append(['xD4'])
            elif cmd1 in [0x10, 0x11, 0x12]:
                v, = struct.unpack("<H", asm[i:i+2])
                i += 2
                para.append(['xD0', cmd1 -0x10, v])
            elif cmd1 in [0x16, 0x17, 0x18]:
                vv = ['xD6', cmd1 -0x16, cmd2]
                if cmd2 < 2:
                    v, = struct.unpack("<H", asm[i:i+2])
                    i += 2
                    vv.append(v)
                para.append(vv)
            elif cmd1 == 4:
                para.append(['xC4', cmd2])
            elif cmd1 == 6:
                para.append(['WAIT', cmd2])
            elif cmd1 == 2:
                para.append(['xC2', cmd2])
            elif cmd1 == 5:
                para.append(['xC5', cmd2])
            elif cmd1 == 3:
                para.append(['xC3'])
            elif cmd1 == 9:
                 para.append(['xC9'])
            else:
                assert False, hex(code)

        elif cmd0 == 0:
            assert intxt, "{},{}".format(i, hex(code))
            txt.write(lib.get(code &0xfff))
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

        for _ in range(ini.linkcnt):
            code, secid, ignore, pp, func = struct.unpack('<2BH2I', f.read(12))
            assert ignore == 0
            para = [[secid, code>>4, code&0xf, func]]

            sec2 = False
            if linksep is not None:
                sec2 = secid >= linksep

            if pp != 0xFFFFFFFF:
                assert (pp, sec2) not in ss, i
                ss.add((pp, sec2))

                if sec2:
                    dst, _ = dec(linkdatas[1][pp - ini.linkbuf:])
                else:
                    dst, _ = dec(linkdatas[0][pp - ini.linkbuf:])
                # try:
                dism(para, lines, dst, lib)
                # except:
                #     with open("{}.{}".format(ini.link, ini.linkid) + ".raw.txt", "wt", encoding='utf-8') as f:
                #         f.writelines(lines)
                #     exit(0)

            cap.append(para)

    name = "{}.{}".format(ini.link, linkids[0])
    with open(name + ".txt", "wt", encoding="utf-8") as f:
        json.dump(cap, f, indent=2, ensure_ascii=False)

    with open(name + ".raw.txt", "wt", encoding='utf-8') as f:
        f.writelines(lines)
