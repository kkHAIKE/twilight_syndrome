import configparser
import sys
from build import build
from fontdec import fontdec
from linkdec import linkdec
from fontlib import (FontLib, dumpsz)
from ini import Ini
from merge import merge
from patch import patch

def main(argv):
    conf = configparser.ConfigParser()
    conf.read(argv[2], encoding="utf-8")
    ini = Ini(conf['project'])

    if argv[1] == 'fontdec':
        fontdec(ini)
    elif argv[1] == 'linkdec':
        linkdec(ini, FontLib(ini))
    elif argv[1] == 'dumpsz': # extract width from exe
        dumpsz(ini, FontLib(ini))
    elif argv[1] == 'merge':
        merge(ini)
    elif argv[1] == 'build':
        build(ini, FontLib(ini))
    elif argv[1] == 'patch':
        patch(ini)
    elif argv[1] == 'test':
        fontlib = FontLib(ini)
        for c in "ユカリチサトミシマ":
            print(fontlib.getr(c))

main(sys.argv)
