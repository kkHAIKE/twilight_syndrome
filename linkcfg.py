import pydot
import json
from collections import defaultdict

def getSel(s: str):
    arr = []
    i = 0
    while True:
        tmp = "<CASE,{}>".format(i)
        idx = s.find(tmp)
        if idx == -1:
            break
        idx += len(tmp)

        idx2 = s.index("<CEND,", idx)
        ss = s[idx: idx2]
        if ss.startswith('<COL,0>:'):
            ss = ss[8:]
        arr.append(ss)

        i += 1
    return arr

class Item:
    def __init__(self, idx: int, arr: list):
        self.idx = idx
        sels = []
        limit = False
        go = False
        fin = None
        for v in arr:
            if v[0] == 'TEXT':
                if '<SEL,' in v[1]:
                    sels = getSel(v[1])
                if '<x8B,' in v[1]:
                    limit = True
            elif v[0] == 'FINGO':
                go = True
            elif v[0] == 'FIN':
                fin = v[1:]
        self.out = []
        if fin is None:
            assert len(arr) == 1
            self.isfin = True
            return
        else:
            self.isfin = False
        if len(fin) == 0:
            return

        dst = defaultdict(list)
        for i, v in enumerate(sels):
            dst[fin[i]].append(v)
        if limit:
            dst[fin[-1]].append('超时')
        if go:
            dst[fin[-1]].append('GO')
        if len(dst) == 1 and list(dst.values())[0][0] == 'GO':
            return

        for k, v in dst.items():
            assert k >= 10
            self.out.append((k-10, " / ".join(v)))

class Block:
    def __init__(self, s: Item):
        self.s = s
        # self.e = s

    def setEnd(self, e: Item):
        self.e = e

    def __repr__(self):
        if self.s == self.e:
            return str(self.s.idx)
        return "{}-{}".format(self.s.idx, self.e.idx)

    @property
    def idx(self):
        return self.s.idx

    @property
    def out(self):
        return self.e.out

    @property
    def isfin(self):
        return self.e.isfin

def mkGraph(fpath):
    with open(fpath, 'rt', encoding='utf-8') as f:
        m = json.load(f)

    itms = []
    outid = set()
    for i, v in enumerate(m):
        itm = Item(i, v)
        itms.append(itm)
        for o in itm.out:
            outid.add(o[0])

    bb = None
    bbm = {}
    for v in itms:
        if bb is None or v.idx in outid:
            bb = Block(v)
            bbm[v.idx] = bb

        bb.setEnd(v)

        if v.out or v.isfin:
            bb = None

    # print(outid)
    # import pprint;pprint.pprint(bbm)

    g = pydot.Dot()
    g.set_node_defaults(shape='box', fontname='SimSun')
    g.set_edge_defaults(fontname='SimSun')

    for v in bbm.values():
        g.add_node(pydot.Node(str(v)))
        if v.out:
            for o in v.out:
                g.add_edge(pydot.Edge(str(v), str(bbm[o[0]]), label=o[1]))
        elif not v.isfin:
            g.add_edge(pydot.Edge(str(v), str(bbm[v.e.idx+1])))

    g.write(fpath + ".dot", encoding='utf-8')

mkGraph(r'..\file0\DAT\CAP1\K1LINK.CDB.20.txt')
