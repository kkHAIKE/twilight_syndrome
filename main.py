from base64 import encode
import configparser
import sys
from fontdec import fontdec
from linkdec import linkdec
from fontlib import (FontLib, dumpsz)
from ini import Ini
from merge import merge

def main(argv):
    conf = configparser.ConfigParser()
    conf.read(argv[2], encoding="utf-8")
    ini = Ini(conf['project'])

    if argv[1] == 'fontdec':
        fontdec(ini)
    elif argv[1] == 'linkdec':
        linkdec(ini, FontLib(ini))
    elif argv[1] == 'dumpsz':
        dumpsz(ini, FontLib(ini))
    elif argv[1] == 'merge':
        merge(ini)
    elif argv[1] == 'test':
        fontlib = FontLib(ini)
        for c in "ユカリチサトミシマ":
            print(fontlib.getr(c))

main(sys.argv)
