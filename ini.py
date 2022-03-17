import configparser
import os

class Ini:
    def __init__(self, proj: configparser.SectionProxy):
        self._proj = proj

    @property
    def exe(self) -> str:
        return os.path.join(self._proj.get('srcdir'), self._proj.get('exe'))

    @property
    def link(self) -> str:
        return os.path.join(self._proj.get('srcdir'), self._proj.get('link'))

    @property
    def font(self) -> str:
        return os.path.join(self._proj.get('srcdir'), self._proj.get('font'))

    @property
    def dstexe(self) -> str:
        return os.path.join(self._proj.get('dstdir'), self._proj.get('exe'))

    @property
    def dstlink(self) -> str:
        return os.path.join(self._proj.get('dstdir'), self._proj.get('link'))

    @property
    def dstfont(self) -> str:
        return os.path.join(self._proj.get('dstdir'), self._proj.get('font'))

    @property
    def fontid(self) -> int:
        return self._proj.getint('fontid')

    def linkid(self) -> tuple:
        arr = [int(x) for x in self._proj.get('linkid').split(',')]
        if len(arr) == 1:
            return [arr[0]], None
        assert len(arr) == 3
        return [arr[0], arr[2]], arr[1]

    def _hex(self, k) -> int:
        return int(self._proj.get(k), 16)

    @property
    def base(self) -> int:
        return self._hex('base')

    @property
    def fontbuf(self) -> int:
        return self._hex('fontbuf')

    @property
    def fonttbl(self) -> int:
        return self._hex('fonttbl')

    @property
    def fontcnt(self) -> int:
        return self._proj.getint('fontcnt')

    @property
    def linkbuf(self) -> int:
        return self._hex('linkbuf')

    @property
    def linktbl(self) -> int:
        return self._hex('linktbl')

    @property
    def linkcnt(self) -> int:
        return self._proj.getint('linkcnt')
