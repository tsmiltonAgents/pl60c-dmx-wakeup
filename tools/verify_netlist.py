"""Check the schematic's exported netlist (build/sch.net) against hw/design.py pin->net table."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'hw'))
from sexp import parse, find, findall
import variant
design = variant.design()
d = design.build(); want = d.nets()
net = parse(open(os.path.join(ROOT, 'build', 'sch_' + variant.BOARD + '.net')).read())[0]
got = {}
for n in findall(find(net, 'nets'), 'net'):
    name = find(n, 'name')[1]
    for node in findall(n, 'node'):
        got.setdefault(name, []).append((find(node, 'ref')[1], str(find(node, 'pin')[1])))
W = {frozenset(v) for v in want.values()}
G = {frozenset(v) for v in got.values() if len(v) > 1}
bad = 0
for s in W - G: print('   MISSING in schematic netlist:', sorted(s)); bad += 1
for s in G - W: print('   EXTRA in schematic netlist:', sorted(s)); bad += 1
print(f'   schematic netlist: {len(G)} multi-pin nets match design ({len(W)})' if not bad else f'   {bad} mismatches')
sys.exit(1 if bad else 0)
