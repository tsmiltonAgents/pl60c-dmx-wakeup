"""Post-route pass:
 1. add stitching vias for GND items KiCad's DRC still reports as unconnected (checked against pads/tracks/vias),
 2. delete GND vias that end up dangling (connected on one layer only) after the final zone fill.
Usage: <kicad python> fix_gnd.py <board.kicad_pcb>"""
import os, sys, json, math, subprocess
import pcbnew
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_pcb import Obstacles, add_via, add_track, _rect_dist
KC = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'

def drc_json(board_path):
    out = board_path + '.drc.json'
    subprocess.run([KC, 'pcb', 'drc', '--format', 'json', '--severity-all', '--output', out, board_path], capture_output=True)
    rep = json.load(open(out)); os.remove(out)
    return rep

def items(v):
    return [(it['pos']['x'], it['pos']['y'], it.get('description', '')) for it in v.get('items', [])]  # positions are mm

def refill_save(board, path):
    filler = pcbnew.ZONE_FILLER(board); filler.Fill(board.Zones())
    pcbnew.SaveBoard(path, board)

def fix(board_path, rounds=4):
    for rnd in range(rounds):
        rep = drc_json(board_path)
        unc = [items(v) for v in rep.get('unconnected_items', [])]
        gnd_pts = []
        for u in unc:
            for (x, y, desc) in u:
                if '[GND]' in desc and desc.startswith(('Pad', 'PTH pad')):
                    gnd_pts.append((x, y, desc))
        print(f'round {rnd}: {len(unc)} unconnected, {len(gnd_pts)} GND anchor items')
        if not gnd_pts:
            break
        board = pcbnew.LoadBoard(board_path)
        gnd = board.FindNet('GND')
        bb = board.GetBoardEdgesBoundingBox(); W, H = bb.GetWidth() / 1e6, bb.GetHeight() / 1e6
        obs = Obstacles(board, W, H)
        added = 0
        for (px, py, desc) in gnd_pts:
            done = False
            for dist in [0.9, 1.2, 1.5, 1.9, 2.4, 3.0, 3.6]:
                for k in range(16):
                    ang = 2 * math.pi * k / 16
                    x, y = px + dist * math.cos(ang), py + dist * math.sin(ang)
                    for w in (0.3, 0.25):
                        if obs.via_ok(x, y) and obs.track_ok((px, py), (x, y), w):
                            add_via(board, gnd, x, y); add_track(board, gnd, px, py, x, y, w); obs.add_via(x, y)
                            added += 1; done = True; break
                    if done: break
                if done: break
            if not done: print(f'  could not stitch {desc} at ({px:.2f},{py:.2f})')
        print(f'  added {added} vias')
        refill_save(board, board_path)
        if added == 0:
            break
    # remove dangling GND vias/tracks (grid vias that landed where only one pour reaches them)
    for rnd in range(4):
        rep = drc_json(board_path)
        dang = [items(v)[0] for v in rep.get('violations', []) if v.get('type') in ('via_dangling', 'track_dangling')]
        dang = [(x, y, desc) for (x, y, desc) in dang if '[GND]' in desc]
        if not dang: break
        board = pcbnew.LoadBoard(board_path)
        removed = 0
        for t in list(board.GetTracks()):
            if t.GetNetname() != 'GND': continue
            if t.GetClass() == 'PCB_VIA':
                vx, vy = t.GetPosition().x / 1e6, t.GetPosition().y / 1e6
                if any(math.hypot(vx - x, vy - y) < 0.05 for (x, y, d) in dang if d.startswith('Via')):
                    board.Remove(t); removed += 1
            else:
                for (x, y, d) in dang:
                    if not d.startswith('Track'): continue
                    for e in (t.GetStart(), t.GetEnd()):
                        if math.hypot(e.x / 1e6 - x, e.y / 1e6 - y) < 0.05:
                            board.Remove(t); removed += 1; break
                    else:
                        continue
                    break
        print(f'removed {removed} dangling GND vias')
        refill_save(board, board_path)
    rep = drc_json(board_path)
    unc = [items(v) for v in rep.get('unconnected_items', [])]
    print('final unconnected:', len(unc))
    for u in unc: print('  ', u)
    return len(unc)

if __name__ == '__main__':
    sys.exit(0 if fix(sys.argv[1]) == 0 else 1)
