"""Post-route pass: find GND items KiCad reports as unconnected (islands in the pour, pads without a path
to the plane) and add stitching vias in free spots near them, checking clearance against pads, tracks and vias.
Usage: <kicad python> fix_gnd.py <board.kicad_pcb>"""
import os, sys, json, math, subprocess
import pcbnew
from pcbnew import VECTOR2I, FromMM
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_pcb import _seg_dist, _pad_geo, add_via, add_track, V
KC = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'

def drc_unconnected(board_path):
    out = board_path + '.drc.json'
    subprocess.run([KC, 'pcb', 'drc', '--format', 'json', '--output', out, board_path], capture_output=True)
    rep = json.load(open(out)); os.remove(out)
    pts = []
    for v in rep.get('unconnected_items', []):
        items = v.get('items', [])
        pts.append([(it['pos']['x'], it['pos']['y'], it.get('description', '')) for it in items])
    return pts

def fix(board_path, rounds=4):
    for rnd in range(rounds):
        unc = drc_unconnected(board_path)
        gnd_unc = [u for u in unc if any('[GND]' in it[2] for it in u)]
        print(f'round {rnd}: {len(unc)} unconnected, {len(gnd_unc)} on GND')
        if not gnd_unc:
            return len(unc)
        board = pcbnew.LoadBoard(board_path)
        gnd = board.FindNet('GND')
        W = board.GetBoardEdgesBoundingBox().GetWidth() / 1e6; H = board.GetBoardEdgesBoundingBox().GetHeight() / 1e6
        obstacles = []   # (kind, geometry, radius)
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                x, y, r = _pad_geo(pad)
                obstacles.append(('pad', pad.GetNetname(), (x, y), r))
        for t in board.GetTracks():
            if t.GetClass() == 'PCB_VIA':
                obstacles.append(('via', t.GetNetname(), (t.GetPosition().x / 1e6, t.GetPosition().y / 1e6), t.GetWidth() / 2e6))
            else:
                obstacles.append(('trk', t.GetNetname(), ((t.GetStart().x / 1e6, t.GetStart().y / 1e6), (t.GetEnd().x / 1e6, t.GetEnd().y / 1e6)), t.GetWidth() / 2e6))
        via_r, clr = 0.35, 0.25
        def clear(x, y):
            if not (1.5 < x < W - 1.5 and 1.5 < y < H - 1.5): return False
            for kind, net, g, r in obstacles:
                if kind == 'trk':
                    dist = _seg_dist((x, y), g[0], g[1])
                else:
                    dist = math.hypot(x - g[0], y - g[1])
                need = r + via_r + (clr if net != 'GND' else 0.1)
                if net == 'GND' and kind == 'pad': need = r + via_r + 0.1
                if dist < need: return False
            return True
        def clear_track(a, b, w=0.3):
            for kind, net, g, r in obstacles:
                if net == 'GND': continue
                if kind == 'trk':
                    # segment-segment distance approx: sample points
                    pts = [(a[0] + (b[0] - a[0]) * k / 8, a[1] + (b[1] - a[1]) * k / 8) for k in range(9)]
                    if min(_seg_dist(pt, g[0], g[1]) for pt in pts) < r + w / 2 + clr: return False
                else:
                    if _seg_dist(g, a, b) < r + w / 2 + clr: return False
            return True
        added = 0
        for u in gnd_unc:
            for (ux, uy, desc) in u:
                if 'Zone' in desc: continue
                px, py = ux / 1e6, uy / 1e6
                done = False
                for dist in [0.9, 1.2, 1.5, 1.9, 2.4, 3.0]:
                    for k in range(16):
                        ang = 2 * math.pi * k / 16
                        x, y = px + dist * math.cos(ang), py + dist * math.sin(ang)
                        if clear(x, y) and clear_track((px, py), (x, y)):
                            add_via(board, gnd, x, y); add_track(board, gnd, px, py, x, y)
                            obstacles.append(('via', 'GND', (x, y), via_r)); added += 1; done = True; break
                    if done: break
                if done: break
        # zone-zone islands: put a via inside the island: use the reported zone point? (KiCad reports zone origin) -> skip
        print(f'  added {added} vias')
        filler = pcbnew.ZONE_FILLER(board); filler.Fill(board.Zones())
        pcbnew.SaveBoard(board_path, board)
        if added == 0:
            break
    unc = drc_unconnected(board_path)
    print('final unconnected:', len(unc))
    for u in unc: print('  ', u)
    return len(unc)

if __name__ == '__main__':
    sys.exit(0 if fix(sys.argv[1]) == 0 else 1)
