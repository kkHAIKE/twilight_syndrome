import struct
import sys

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
        n = (len(data) + 2047) // 2048
        on = self.head[idx][1]
        assert n <= on, "{},{}".format(n, on)

        self._seek(idx)
        self._f.write(data)

def main(argv):
    db = CDB(argv[1])
    idx = int(argv[2])
    fpath = "{}.{}.bin".format(argv[1], idx)
    with open(fpath, "rb") as f:
        data = f.read()
    db.write(idx, data)

if __name__ == '__main__':
    main(sys.argv)
