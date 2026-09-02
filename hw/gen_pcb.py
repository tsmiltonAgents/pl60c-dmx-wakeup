"""Build the KiCad PCB (unrouted) from design.py using the pcbnew Python API.
Run with KiCad's bundled python (it has the pcbnew module)."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from pcbnew import VECTOR2I, FromMM
import design
from kicad_libs import footprint_path

def V(x, y):
    return VECTOR2I(FromMM(x), FromMM(y))

def add_line(board, layer, x1, y1, x2, y2, w=0.1):
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(V(x1, y1)); s.SetEnd(V(x2, y2)); s.SetLayer(layer); s.SetWidth(FromMM(w)); board.Add(s)

def add_arc(board, layer, cx, cy, r, a0, a1, w=0.1):
    """Arc from angle a0 to a1 (degrees, screen coords: y down) around (cx,cy)."""
    s = pcbnew.PCB_SHAPE(board); s.SetShape(pcbnew.SHAPE_T_ARC)
    am = math.radians((a0 + a1) / 2)
    p0 = V(cx + r * math.cos(math.radians(a0)), cy + r * math.sin(math.radians(a0)))
    pm = V(cx + r * math.cos(am), cy + r * math.sin(am))
    p1 = V(cx + r * math.cos(math.radians(a1)), cy + r * math.sin(math.radians(a1)))
    s.SetArcGeometry(p0, pm, p1); s.SetLayer(layer); s.SetWidth(FromMM(w)); board.Add(s)

def add_text(board, txt, x, y, layer=pcbnew.F_SilkS, size=1.0, thick=0.15, rot=0, mirror=False, bold=False):
    t = pcbnew.PCB_TEXT(board); t.SetText(txt); t.SetPosition(V(x, y)); t.SetLayer(layer)
    t.SetTextSize(VECTOR2I(FromMM(size), FromMM(size))); t.SetTextThickness(FromMM(thick))
    t.SetTextAngleDegrees(rot); t.SetMirrored(mirror); t.SetBold(bold)
    board.Add(t)

def outline(board, w, h, r):
    add_line(board, pcbnew.Edge_Cuts, r, 0, w - r, 0)
    add_line(board, pcbnew.Edge_Cuts, w, r, w, h - r)
    add_line(board, pcbnew.Edge_Cuts, w - r, h, r, h)
    add_line(board, pcbnew.Edge_Cuts, 0, h - r, 0, r)
    add_arc(board, pcbnew.Edge_Cuts, w - r, r, r, -90, 0)
    add_arc(board, pcbnew.Edge_Cuts, w - r, h - r, r, 0, 90)
    add_arc(board, pcbnew.Edge_Cuts, r, h - r, r, 90, 180)
    add_arc(board, pcbnew.Edge_Cuts, r, r, r, 180, 270)

def add_zone(board, layer, net, pts, name='', priority=0, keepout=False):
    z = pcbnew.ZONE(board)
    z.SetLayer(layer)
    if keepout:
        z.SetIsRuleArea(True); z.SetDoNotAllowZoneFills(True); z.SetDoNotAllowTracks(True); z.SetDoNotAllowVias(True)
        z.SetDoNotAllowFootprints(False); z.SetDoNotAllowPads(False)
        ls = pcbnew.LSET(); ls.AddLayer(pcbnew.F_Cu); ls.AddLayer(pcbnew.B_Cu); z.SetLayerSet(ls)
    else:
        z.SetNet(net)
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetMinThickness(FromMM(0.25)); z.SetLocalClearance(FromMM(0.3))
        z.SetThermalReliefGap(FromMM(0.4)); z.SetThermalReliefSpokeWidth(FromMM(0.4))
        z.SetAssignedPriority(priority)
    z.SetZoneName(name)
    ol = z.Outline(); ol.NewOutline()
    for (x, y) in pts:
        ol.Append(FromMM(x), FromMM(y))
    board.Add(z)
    return z

def build(out_path):
    d = design.build()
    W, H, R = d.board['w'], d.board['h'], d.board['corner']
    board = pcbnew.BOARD()
    board.SetFileName(out_path)
    # ---------------- design rules (JLCPCB 2-layer capability with margin) ----------------
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = FromMM(0.15); ds.m_ViasMinSize = FromMM(0.5); ds.m_MinThroughDrill = FromMM(0.3)
    ds.m_MinClearance = FromMM(0.15); ds.m_CopperEdgeClearance = FromMM(0.3); ds.m_HoleClearance = FromMM(0.25)
    ds.m_MinSilkTextHeight = FromMM(0.8); ds.m_HoleToHoleMin = FromMM(0.5)
    ns = ds.m_NetSettings
    dflt = ns.GetDefaultNetclass()
    dflt.SetClearance(FromMM(0.2)); dflt.SetTrackWidth(FromMM(0.25)); dflt.SetViaDiameter(FromMM(0.7)); dflt.SetViaDrill(FromMM(0.35))
    pwr = pcbnew.NETCLASS('Power')
    pwr.SetClearance(FromMM(0.2)); pwr.SetTrackWidth(FromMM(0.5)); pwr.SetViaDiameter(FromMM(0.8)); pwr.SetViaDrill(FromMM(0.4))
    ns.SetNetclass('Power', pwr)
    for n in ['+5V', '+3V3', 'VBUS', 'GND']:
        ns.SetNetclassPatternAssignment(n, 'Power')
    # ---------------- nets ----------------
    nets = {}
    for name in sorted(d.nets()):
        ni = pcbnew.NETINFO_ITEM(board, name); board.Add(ni); nets[name] = ni
    # ---------------- footprints ----------------
    for p in d.parts:
        lib, name = footprint_path(p.footprint)
        fp = pcbnew.FootprintLoad(lib, name)
        if fp is None:
            raise SystemExit(f'footprint not found: {p.footprint}')
        fp.SetReference(p.ref); fp.SetValue(p.value)
        fp.SetField('LCSC', p.lcsc or ''); fp.SetField('MPN', p.mpn or '')
        if p.lcsc: fp.GetField('LCSC').SetVisible(False)
        if p.mpn: fp.GetField('MPN').SetVisible(False)
        fp.SetPath(pcbnew.KIID_PATH('/' + d.sch_uuid + '/' + p.uuid))
        fp.SetPosition(V(*p.pcb_pos))
        if p.side == 'bottom':
            fp.Flip(fp.GetPosition(), False)
        fp.SetOrientationDegrees(p.pcb_rot)
        if p.dnp:
            fp.SetDNP(True)
        fp.Value().SetVisible(False)
        # make refs small
        fp.Reference().SetTextSize(VECTOR2I(FromMM(0.8), FromMM(0.8))); fp.Reference().SetTextThickness(FromMM(0.12))
        for pad in fp.Pads():
            net = p.pins.get(pad.GetNumber())
            if net:
                pad.SetNet(nets[net])
        board.Add(fp)
        p._fp = fp
    # ---------------- outline ----------------
    outline(board, W, H, R)
    # ---------------- zones: GND pour both sides ----------------
    m = 0.5
    rect = [(m, m), (W - m, m), (W - m, H - m), (m, H - m)]
    add_zone(board, pcbnew.F_Cu, nets['GND'], rect, 'GND_F')
    add_zone(board, pcbnew.B_Cu, nets['GND'], rect, 'GND_B')
    # antenna keep-out: 15 mm around the module antenna, inside the board (antenna itself hangs off the top edge)
    u1 = d.by_ref('U1'); ux, uy = u1.pcb_pos
    for (x1, y1, x2, y2) in d.keepouts:
        add_zone(board, pcbnew.F_Cu, None, [(x1, y1), (x2, y1), (x2, y2), (x1, y2)], 'keepout', keepout=True)
    # ---------------- silkscreen ----------------
    for (txt, x, y, size, rot, layer, mirror) in d.silk:
        layer = board.GetLayerID(layer) if isinstance(layer, str) else layer
        add_text(board, txt, x, y, layer=layer, size=size, thick=max(0.12, size * 0.15), rot=rot, mirror=mirror)
    pcbnew.SaveBoard(out_path, board)
    return board, d

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pcb', 'pl60c_dmx.kicad_pcb')
    board, d = build(out)
    print('wrote', out, 'footprints', len(board.GetFootprints()), 'nets', board.GetNetCount())
    # report placement bounding boxes for sanity
    for p in d.parts:
        bb = p._fp.GetBoundingBox(False, False)
        print(f"{p.ref:4s} x[{bb.GetLeft()/1e6:6.2f},{bb.GetRight()/1e6:6.2f}] y[{bb.GetTop()/1e6:6.2f},{bb.GetBottom()/1e6:6.2f}]")
