import struct
import sys
import io

class CDB:
    def __init__(self, fpath):
        self._f = open(fpath, "rb+")
        self.head = self._head()

    def __del__(self):
        self._f.close()

    def _head(self):
        r = []
        while True:
            p, = struct.unpack("<H", self._f.read(2))
            if p == 0:
                break

            l, = struct.unpack("<H", self._f.read(2))
            r.append((p, l))
        return r

    def _seek(self, idx):
        self._f.seek(self.head[idx][0] * 2048)

    def read(self, idx):
        self._seek(idx)
        return self._f.read(self.head[idx][1] * 2048)

    def write(self, idx, data):
        # pad
        if len(data) % 2048 != 0:
            data += b'\0' * (2048 - (len(data) % 2048))

        n = len(data) // 2048
        on = self.head[idx][1]
        print(on, "->", n)

        self._seek(idx)

        ext = None
        if n > on:
            # 扩张，读取后面的
            self._f.seek(on*2048, io.SEEK_CUR)
            ext = self._f.read()
            self._seek(idx)

        self._f.write(data)

        for _ in range(on*2048 - len(data)):
            self._f.write(b'\0')

        if ext is not None:
            self._f.write(ext)

            # 修正头部
            self._f.seek(0)
            for p, l in self.head:
                if p > self.head[idx][0]:
                    p += n - on
                elif p == self.head[idx][0]:
                    l = n
                self._f.write(struct.pack("<2H", p, l))

def main(argv):
    db = CDB(argv[1])
    idx = int(argv[2])
    fpath = "{}.{}.bin".format(argv[1], idx)
    with open(fpath, "rb") as f:
        data = f.read()
    db.write(idx, data)

if __name__ == '__main__':
    main(sys.argv)
