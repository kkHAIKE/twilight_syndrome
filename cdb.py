import struct

class CDB:
    def __init__(self, fpath):
        self._f = open(fpath, "rb")
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

    def read(self, idx):
        self._f.seek(self.head[idx][0] * 2048)
        return self._f.read(self.head[idx][1] * 2048)
