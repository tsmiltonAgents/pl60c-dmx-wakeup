"""Manufacturing outputs: Gerbers + drill (JLCPCB settings), JLCPCB BOM + CPL, PDFs, renders, summary.
Run with KiCad's bundled python:  <kicad python> tools/export.py"""
import os, sys, csv, re, json, subprocess, shutil, zipfile, datetime
import pcbnew
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'hw'))
import design
KC = '/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
PCB = os.path.join(ROOT, 'pcb', 'pl60c_dmx.kicad_pcb')
SCH = os.path.join(ROOT, 'pcb', 'pl60c_dmx.kicad_sch')
OUT = os.path.join(ROOT, 'production')
GERB = os.path.join(OUT, 'gerbers')

def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    err = '\n'.join(l for l in (r.stdout + r.stderr).splitlines() if 'Fontconfig' not in l and 'Debug:' not in l and 'assert' not in l)
    if r.returncode != 0:
        raise SystemExit(f'command failed: {" ".join(cmd)}\n{err}')
    return err

def gerbers():
    shutil.rmtree(GERB, ignore_errors=True); os.makedirs(GERB)
    layers = 'F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts'
    run([KC, 'pcb', 'export', 'gerbers', '--output', GERB + '/', '--layers', layers, '--no-x2', '--no-netlist',
         '--subtract-soldermask', '--check-zones', PCB])   # protel extensions (JLCPCB preferred) are the default
    run([KC, 'pcb', 'export', 'drill', '--output', GERB + '/', '--format', 'excellon', '--drill-origin', 'absolute',
         '--excellon-units', 'mm', '--excellon-zeros-format', 'decimal', '--excellon-separate-th', '--generate-map', '--map-format', 'gerberx2', PCB])
    zpath = os.path.join(OUT, 'pl60c_dmx_gerbers.zip')
    with zipfile.ZipFile(zpath, 'w', zipfile.ZIP_DEFLATED) as z:
        for f in sorted(os.listdir(GERB)):
            z.write(os.path.join(GERB, f), f)
    return sorted(os.listdir(GERB))

def load_rotation_db():
    db = []
    with open(os.path.join(ROOT, 'tools', 'cpl_rotations_db.csv')) as f:
        for row in csv.reader(f):
            if not row or row[0].startswith('Footprint pattern'): continue
            db.append((re.compile(row[0]), float(row[1])))
    return db

def bom_cpl(d):
    board = pcbnew.LoadBoard(PCB)
    rotdb = load_rotation_db()
    parts = {p.ref: p for p in d.parts}
    groups = {}
    cpl = []
    notes = []
    for fp in board.GetFootprints():
        ref = fp.GetReference(); p = parts[ref]
        if not p.lcsc or p.dnp:
            if p.dnp: notes.append(f'{ref} is DNP (not placed): {p.desc}')
            continue
        fpname = fp.GetFPID().GetLibItemName().wx_str() if hasattr(fp.GetFPID().GetLibItemName(), 'wx_str') else str(fp.GetFPID().GetLibItemName())
        key = (p.value, fpname, p.lcsc)
        groups.setdefault(key, []).append(ref)
        pos = fp.GetPosition(); rot = fp.GetOrientationDegrees()
        corr = 0.0
        for rx, r in rotdb:
            if rx.search(fpname):
                corr = r; break
        jrot = (rot + corr + p.jlc_rot) % 360
        layer = 'Top' if not fp.IsFlipped() else 'Bottom'
        cpl.append((ref, round(pos.x / 1e6, 4), round(-pos.y / 1e6, 4), layer, round(jrot, 1), round(rot % 360, 1)))
    with open(os.path.join(OUT, 'pl60c_dmx_bom_jlcpcb.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['Comment', 'Designator', 'Footprint', 'LCSC Part #'])
        for (val, fpn, lcsc), refs in sorted(groups.items(), key=lambda kv: kv[1][0]):
            w.writerow([val, ','.join(sorted(refs, key=lambda r: (re.sub(r'\d', '', r), int(re.sub(r'\D', '', r) or 0)))), fpn, lcsc])
    for fname, idx in (('pl60c_dmx_cpl_jlcpcb.csv', 4), ('pl60c_dmx_cpl_kicad_rotation.csv', 5)):
        with open(os.path.join(OUT, fname), 'w', newline='') as f:
            w = csv.writer(f); w.writerow(['Designator', 'Mid X', 'Mid Y', 'Layer', 'Rotation'])
            for row in sorted(cpl, key=lambda r: (re.sub(r'\d', '', r[0]), int(re.sub(r'\D', '', r[0]) or 0))):
                w.writerow(list(row[:4]) + [row[idx]])
    # full engineering BOM (every part incl. DNP / no-LCSC)
    with open(os.path.join(OUT, 'pl60c_dmx_bom_full.csv'), 'w', newline='') as f:
        w = csv.writer(f); w.writerow(['Ref', 'Value', 'MPN', 'LCSC', 'Footprint', 'DNP', 'Description'])
        for p in sorted(d.parts, key=lambda p: (re.sub(r'\d', '', p.ref), int(re.sub(r'\D', '', p.ref) or 0))):
            w.writerow([p.ref, p.value, p.mpn, p.lcsc, p.footprint, 'yes' if p.dnp else '', p.desc])
    return groups, cpl, notes

def docs():
    run([KC, 'sch', 'export', 'pdf', '--output', os.path.join(OUT, 'pl60c_dmx_schematic.pdf'), SCH])
    run([KC, 'pcb', 'export', 'pdf', '--output', os.path.join(OUT, 'pl60c_dmx_pcb_top.pdf'), '--layers', 'F.Cu,F.SilkS,F.Mask,Edge.Cuts', '--include-border-title', PCB])
    run([KC, 'pcb', 'export', 'pdf', '--output', os.path.join(OUT, 'pl60c_dmx_pcb_bottom.pdf'), '--layers', 'B.Cu,B.SilkS,B.Mask,Edge.Cuts', '--mirror', '--include-border-title', PCB])
    for side in ('top', 'bottom'):
        run([KC, 'pcb', 'render', '--output', os.path.join(OUT, f'render_{side}.png'), '--side', side, '--width', '1800', '--height', '1200', '--zoom', '1.1', '--quality', 'high', PCB])
    run([KC, 'pcb', 'export', 'step', '--output', os.path.join(OUT, 'pl60c_dmx.step'), '--subst-models', PCB])

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    d = design.build()
    files = gerbers()
    groups, cpl, notes = bom_cpl(d)
    docs()
    summary = dict(generated=datetime.datetime.now().isoformat(timespec='seconds'), gerber_files=files,
                   bom_lines=len(groups), placed_parts=len(cpl), notes=notes)
    json.dump(summary, open(os.path.join(OUT, 'summary.json'), 'w'), indent=1)
    print(json.dumps(summary, indent=1))
