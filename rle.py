from typing import Optional
import io
import binascii

def dec(d):
    r = bytearray()
    i = 0
    while i < len(d):
        c = d[i]
        i += 1

        if c < 128:
            # 不重复
            c += 1
            r.extend(d[i:i+c])
            i += c
        elif c < 192:
            # 重复
            c -= 125
            for _ in range(c):
                r.append(d[i])
            i += 1
        elif c < 224:
            # 重复之前的
            c -= 188
            p = (d[i] << 8) | d[i+1]
            r.extend(r[len(r)-p:len(r)-p+c])
            i += 2
        elif c < 240:
            # 递增值
            c -= 220
            for j in range(c):
                r.append((d[i+1] + j*d[i]) &0xff)
            i += 2
        elif c == 255:
            break
        else:
            assert False
    return r, d[i:]

# 递增值 19
# 重复之前的 35
# 重复 66
# 不重复 128

class Range:
    def __init__(self, tp, sz, enc):
        self.tp = tp
        self.sz = sz
        self.enc = enc
        self.pos = -1

    def setStart(self, pos):
        self.pos = pos

    # +1
    @property
    def end(self):
        return self.pos + self.sz

    def __repr__(self) -> str:
        return "tp:{}, sz:{}, enc:{}".format(self.tp, self.sz, binascii.b2a_hex(self.enc))

    # @property
    # def low(self):
    #     if self.tp == 1:
    #         return 2
    #     if self.tp >= 2:
    #         return 3
    #     assert False

    # @property
    # def isLow(self):
    #     return self.sz == self.low

class RangeMap:
    def __init__(self):
        self._m = {}

    def add2(self, r: Range):
        left, right = self.get(r.pos), self.get(r.end -1)
        for i in range(r.pos+1, r.end-1):
            assert self.get(i) is None

        if left is None and right is None:
            self.put(r)
            return True

        dif = 0
        if left is not None:
            if left.sz-1 < 3:
                leftOver = False
                dif -= 1
            else:
                leftOver = True
        if right is not None:
            if right.sz-1 < 3:
                rightOver = False
                dif -= 1
            else:
                rightOver = True

        if r.sz + dif < 4:
            return False

        if left is not None:
            if leftOver:
                left.sz -= 1
            else:
                r.setStart(r.pos + 1)
                r.sz -= 1
        if right is not None:
            if rightOver:
                right.setStart(right.pos + 1)
                right.sz -= 1
            else:
                r.sz -= 1
        self.put(r)
        return True

    def add(self, r: Range):
        assert r.pos != -1
        if r.tp == 2:
            return self.add2(r)

        # 先探测
        needRm = set()
        #for i in range(r.pos, r.end):
        i = r.pos
        while i < r.end:
            nr = self.get(i)
            if nr is None:
                i += 1
                continue
            # if nr in needRm:
            #     continue

            # 和他一样，或者比他小，直接不考虑
            if r.pos >= nr.pos and r.end <= nr.end:
                return False

            # 特殊情况
            if nr.tp == 1 and ( \
                (r.pos == nr.pos-1 and r.end == nr.end) or \
                (r.pos == nr.pos and r.end == nr.end+1)):
                return False

            # 比他大
            if r.pos <= nr.pos and r.end >= nr.end:
                needRm.add(nr)
                # i += nr.sz
                i = nr.end
                continue

            # 如果 nr 是低保
            # if nr.isLow:
            #     needRm.add(nr)
            #     i = nr.end
            #     continue

            # 其他相交
            return False

        # 清理
        for nr in needRm:
            self.rm(nr)

        self.put(r)
        return True

    def get(self, pos) -> Optional[Range]:
        return self._m.get(pos, None)

    def rm(self, r: Range):
        for i in range(r.pos, r.end):
            del self._m[i]

    def put(self, r: Range):
        for i in range(r.pos, r.end):
            self._m[i] = r

# 获取最大的递增队列
def getIncr(d) -> Optional[Range]:
    if len(d) < 4:
        return None
    dif = d[1] - d[0]
    if dif == 0:
        return None
    if dif < 0:
        dif += 256
    for i in range(2, min(len(d), 19)):
        if (d[i-1] + dif) &0xff != d[i]:
            i -= 1
            break
    i += 1
    if i < 4:
        return None
    return Range(2, i, bytearray([i + 220, dif, d[0]]))

def getRepeat(d) -> Optional[Range]:
    if len(d) < 3:
        return None
    for i in range(1, min(len(d), 66)):
        if d[i] != d[0]:
            i -= 1
            break
    i += 1
    if i < 3:
        return None
    return Range(1, i, bytearray([i + 125, d[0]]))

# 从 min(一半大小开始, 35) -> 4
def markSame(m: RangeMap, d: bytes, sz):
    #for i in range(len(d)-sz, sz-1, -1):
    i = len(d)-sz
    while i >= sz:
        tmp = d[i: i+sz]
        r = d[i-65535: i]

        idx = r.rfind(tmp)
        if idx == -1:
            i -= 1
            continue

        dif = len(r) - idx
        r = Range(sz, sz, bytearray([sz + 188, dif >> 8, dif &0xff]))
        r.setStart(i)
        if m.add(r):
            i -= sz
        else:
            i -= 1

def writePlain(dst: bytearray, plain: bytearray):
    # 最大长度 128
    n = len(plain) // 128
    for i in range(n):
        dst.append(127)
        dst.extend(plain[i*128: (i+1)*128])
    last = len(plain) % 128
    if last > 0:
        dst.append(last-1)
        dst.extend(plain[-last:])

def enc(d: bytes):
    m = RangeMap()

    # 先标记 重复
    i = 0
    p = 0
    arr = []
    while i < len(d):
        r = getRepeat(d[i:])
        if r is None:
            i += 1
            continue

        r.setStart(i)
        assert m.add(r)

        if i > p:
            arr.append((p, i))
        i += r.sz
        p = i
    if len(d) > p:
        arr.append((p, len(d)))

    # 标记递增
    for ss, ee in arr:
        i = max(ss - 1, 0)
        while i < min(ee + 1, len(d)):
            r = getIncr(d[i:ee])
            if r is None:
                i += 1
                continue

            r.setStart(i)
            if m.add(r):
                i += r.sz
            else:
                i += 1

    # 标记之前
    for i in range(min(len(d) // 2, 35), 3, -1):
        markSame(m, d, i)

    dst = bytearray()
    plain: Optional[bytearray] = None
    i = 0
    while i < len(d):
        r = m.get(i)
        if r is None:
            if plain is None:
                plain = bytearray()
            plain.append(d[i])
            i += 1
            continue

        # 低保转化
        # if r.isLow and plain is not None and len(plain)%128 > 0 and len(plain)%128 <= 128-r.low:
        #     plain.extend(d[r.pos: r.end])
        #     # i += r.sz
        #     i = r.end
        #     continue

        if plain is not None:
            assert len(plain) > 0
            # print('plain', binascii.b2a_hex(plain))
            writePlain(dst, plain)
            plain = None

        dst.extend(r.enc)
        # print('enc', r.tp, binascii.b2a_hex(r.enc))
        # i += r.sz
        i = r.end

    # 收尾
    if plain is not None:
        assert len(plain) > 0
        # print('plain', binascii.b2a_hex(plain))
        writePlain(dst, plain)

    # 结束
    dst.append(0xff)
    return dst

def test():
    with open('../file0/DAT/FONT/KFONT.CDB.0.bin', "rb") as f:
        data = f.read()
    assert len(data) % (8*16) == 0

    encmem = io.BytesIO()
    for i in range(0, len(data), 8*16):
        encmem.write(enc(data[i:i+8*16]))
        # break

    encdata = encmem.getvalue()
    decmem = io.BytesIO()
    while True:
        tmp, encdata = dec(encdata)
        if not tmp:
            break

        decmem.write(tmp)

    print(len(encmem.getvalue()), len(data))
    assert decmem.getvalue() == data
