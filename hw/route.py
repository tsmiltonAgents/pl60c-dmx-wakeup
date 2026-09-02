"""Autoroute the board with Freerouting, import the result, fill zones, save.
Usage: <kicad python> route.py <board.kicad_pcb> [passes]"""
import os, sys, subprocess, shutil
import pcbnew
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JAVA = '/opt/homebrew/opt/openjdk/bin/java'
JAR = os.path.join(ROOT, 'tools', 'freerouting.jar')

def route(board_path, passes=40):
    build = os.path.join(ROOT, 'build'); os.makedirs(build, exist_ok=True)
    base = os.path.splitext(os.path.basename(board_path))[0]
    dsn = os.path.join(build, base + '.dsn'); ses = os.path.join(build, base + '.ses')
    board = pcbnew.LoadBoard(board_path)
    # Route GND with real tracks too: take the pours out of the DSN so the router does not assume a plane,
    # then put them back and fill after import. The pour then only adds copper on top of a complete routing.
    # outer-layer pours are removed (router must make real connections); inner planes stay as DSN planes
    zones = [z for z in board.Zones() if z.GetZoneName() != 'plane']
    for z in zones:
        board.Remove(z)
    # export with a slightly larger clearance than the DRC rule so rounding in the router never trips DRC
    ns = board.GetDesignSettings().m_NetSettings
    for nc in [ns.GetDefaultNetclass()] + [ns.GetNetClassByName(n) for n in ['Power']]:
        nc.SetClearance(nc.GetClearance() + pcbnew.FromMM(0.03))
    assert pcbnew.ExportSpecctraDSN(board, dsn), 'DSN export failed'
    for nc in [ns.GetDefaultNetclass()] + [ns.GetNetClassByName(n) for n in ['Power']]:
        nc.SetClearance(nc.GetClearance() - pcbnew.FromMM(0.03))
    if os.path.exists(ses): os.remove(ses)
    cmd = [JAVA, '-Djava.awt.headless=true', '-jar', JAR, '-de', dsn, '-do', ses, '-mp', str(passes), '-mt', '6',
           '-l', 'en']
    print(' '.join(cmd))
    log = open(os.path.join(build, 'freerouting.log'), 'w')
    r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, timeout=3600)
    log.close()
    if not os.path.exists(ses):
        print(open(os.path.join(build, 'freerouting.log')).read()[-3000:])
        raise SystemExit('freerouting produced no .ses')
    assert pcbnew.ImportSpecctraSES(board, ses), 'SES import failed'
    for z in zones:
        board.Add(z)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(board_path, board)
    n_tracks = sum(1 for t in board.GetTracks() if t.GetClass() == 'PCB_TRACK')
    n_vias = sum(1 for t in board.GetTracks() if t.GetClass() == 'PCB_VIA')
    print(f'routed: {n_tracks} track segments, {n_vias} vias')

if __name__ == '__main__':
    route(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 40)
