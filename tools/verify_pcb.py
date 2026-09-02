"""Check the PCB's pad->net assignments against hw/design.py (schematic/PCB consistency) and report routing stats."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'hw'))
import pcbnew, variant
design = variant.design()
d = design.build(); want = d.nets()
for p in d.parts:
    for pin, net in p.extra_pads.items():
        want.setdefault(net, []).append((p.ref, pin))
board = pcbnew.LoadBoard(os.path.join(ROOT, 'pcb', variant.BOARD + '.kicad_pcb'))
got = {}
for fp in board.GetFootprints():
    for pad in fp.Pads():
        if pad.GetNetname():
            got.setdefault(pad.GetNetname(), set()).add((fp.GetReference(), pad.GetNumber()))
W = {frozenset(v) for v in want.values()}; G = {frozenset(v) for v in got.values()}
bad = 0
for s in W - G: print('   MISSING on PCB:', sorted(s)); bad += 1
for s in G - W: print('   EXTRA on PCB:', sorted(s)); bad += 1
print(f'   PCB pad nets match design: {len(G)} nets' if not bad else f'   {bad} mismatches')
conn = board.GetConnectivity()
print(f'   unrouted connections (ratsnest): {conn.GetUnconnectedCount(True)}')
tracks = [t for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK']; vias = [t for t in board.GetTracks() if t.GetClass() == 'PCB_VIA']
print(f'   {len(tracks)} track segments, {len(vias)} vias, {len(board.GetFootprints())} footprints, {board.GetNetCount() - 1} nets')
sys.exit(1 if bad else 0)
