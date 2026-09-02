"""Build the KiCad PCB (unrouted) from design.py using the pcbnew Python API.
Run with KiCad's bundled python (it has the pcbnew module)."""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pcbnew
from pcbnew import VECTOR2I, FromMM
import variant
design = variant.design()
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

def _seg_dist(p, a, b):
    """Distance from point p to segment ab (all mm tuples)."""
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay
    if dx == 0 and dy == 0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))

def _rect_dist(p, rect):
    """Distance from point p to axis-aligned rect (x1,y1,x2,y2); 0 if inside."""
    x1, y1, x2, y2 = rect
    dx = max(x1 - p[0], 0, p[0] - x2); dy = max(y1 - p[1], 0, p[1] - y2)
    return math.hypot(dx, dy)

def _pad_rect(pad):
    bb = pad.GetBoundingBox()
    return (bb.GetLeft() / 1e6, bb.GetTop() / 1e6, bb.GetRight() / 1e6, bb.GetBottom() / 1e6)

def _pad_geo(pad):
    pos = pad.GetPosition(); sz = pad.GetSize()
    r = math.hypot(sz.x, sz.y) / 2 / 1e6
    return (pos.x / 1e6, pos.y / 1e6, r)

def add_via(board, net, x, y, dia=0.7, drill=0.35):
    v = pcbnew.PCB_VIA(board); v.SetPosition(V(x, y)); v.SetWidth(FromMM(dia)); v.SetDrill(FromMM(drill))
    v.SetViaType(pcbnew.VIATYPE_THROUGH); v.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu); v.SetNet(net); board.Add(v)
    return v

def pad_layer(pad):
    return pcbnew.B_Cu if pad.IsOnLayer(pcbnew.B_Cu) and not pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.F_Cu

def add_track(board, net, x1, y1, x2, y2, w=0.3, layer=pcbnew.F_Cu):
    t = pcbnew.PCB_TRACK(board); t.SetStart(V(x1, y1)); t.SetEnd(V(x2, y2)); t.SetWidth(FromMM(w)); t.SetLayer(layer); t.SetNet(net); board.Add(t)
    return t

class Obstacles:
    """Geometry of everything a new GND via/track must keep clear of (pads, tracks, vias of other nets)."""
    def __init__(self, board, W, H, clearance=0.25, via_dia=0.7, edge=1.2):
        self.W, self.H, self.clr, self.via_r, self.edge = W, H, clearance, via_dia / 2, edge
        self.rects, self.segs, self.circles = [], [], []
        self.gnd_vias = []
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname() != 'GND':
                    self.rects.append(_pad_rect(pad))
                elif pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                    self.circles.append((pad.GetPosition().x / 1e6, pad.GetPosition().y / 1e6, max(pad.GetSize().x, pad.GetSize().y) / 2e6, 'GND'))
        for t in board.GetTracks():
            if t.GetClass() == 'PCB_VIA':
                self.circles.append((t.GetPosition().x / 1e6, t.GetPosition().y / 1e6, t.GetWidth() / 2e6, t.GetNetname()))
            else:
                self.segs.append(((t.GetStart().x / 1e6, t.GetStart().y / 1e6), (t.GetEnd().x / 1e6, t.GetEnd().y / 1e6), t.GetWidth() / 2e6, t.GetNetname()))
    def via_ok(self, x, y, extra=0.0):
        if not (self.edge < x < self.W - self.edge and self.edge < y < self.H - self.edge): return False
        need = self.via_r + self.clr + extra
        for r in self.rects:
            if _rect_dist((x, y), r) < need: return False
        for (a, b, hw, net) in self.segs:
            if _seg_dist((x, y), a, b) < hw + (need if net != 'GND' else self.via_r + 0.1): return False
        for (cx, cy, r, net) in self.circles:
            if math.hypot(x - cx, y - cy) < r + (need if net != 'GND' else self.via_r + 0.15): return False
        return True
    def track_ok(self, a, b, w=0.3):
        pts = [(a[0] + (b[0] - a[0]) * k / 10, a[1] + (b[1] - a[1]) * k / 10) for k in range(11)]
        need = w / 2 + self.clr
        for r in self.rects:
            if min(_rect_dist(p, r) for p in pts) < need: return False
        for (s0, s1, hw, net) in self.segs:
            if net == 'GND': continue
            if min(_seg_dist(p, s0, s1) for p in pts) < hw + need: return False
        for (cx, cy, r, net) in self.circles:
            if net == 'GND': continue
            if _seg_dist((cx, cy), a, b) < r + need: return False
        return True
    def add_via(self, x, y):
        self.circles.append((x, y, self.via_r, 'GND'))

def stitch_pad(board, obs, gnd, pad, fp):
    """Try to place a via next to a GND SMD pad joined by a short track. Returns True on success."""
    px, py = pad.GetPosition().x / 1e6, pad.GetPosition().y / 1e6
    rect = _pad_rect(pad)
    hx, hy = (rect[2] - rect[0]) / 2, (rect[3] - rect[1]) / 2
    c = fp.GetPosition(); ax, ay = px - c.x / 1e6, py - c.y / 1e6
    # cardinal directions first, ordered by how far the pad sits from the footprint centre along that axis
    cards = sorted([(1, 0), (-1, 0), (0, 1), (0, -1)], key=lambda d: -(d[0] * ax + d[1] * ay))
    diags = [(0.707, 0.707), (-0.707, 0.707), (0.707, -0.707), (-0.707, -0.707)]
    for (ux, uy) in cards + diags:
        half = abs(ux) * hx + abs(uy) * hy
        for extra in (0.75, 1.0, 1.3, 1.7, 2.2):
            x, y = px + ux * (half + extra), py + uy * (half + extra)
            for w in (0.3, 0.25):
                if obs.via_ok(x, y) and obs.track_ok((px, py), (x, y), w):
                    add_via(board, gnd, x, y); add_track(board, gnd, px, py, x, y, w, pad_layer(pad)); obs.add_via(x, y)
                    return True
    return False

def preroute_usb(board, fp, nets, W, d_vbus=5.4):
    """Escape routing for the 16-pin USB-C receptacle. Pad row is vertical; 'in' = towards the board interior.
    D+ : A6 (inner) leaves under the connector body to a via, crosses on B.Cu, joins B6's track at a via.
    D- : B7 and A7 leave towards the interior and are joined by a short vertical link (the A6 lane is free there).
    VBUS: both pad pairs leave to vias, joined on B.Cu.  CC1/CC2: straight stubs."""
    P = {}
    for pad in fp.Pads():
        P[pad.GetNumber()] = (pad.GetPosition().x / 1e6, pad.GetPosition().y / 1e6)
    # row axis u: from A6 towards B6 ; interior normal n: perpendicular, pointing at the footprint centre's far side
    ax, ay = P['A6']; bx, by = P['B6']
    ul = math.hypot(bx - ax, by - ay); u = ((bx - ax) / ul, (by - ay) / ul)
    c = fp.GetPosition(); cx, cy = c.x / 1e6, c.y / 1e6
    n = (-u[1], u[0])
    if (ax - cx) * n[0] + (ay - cy) * n[1] < 0:   # make n point away from the connector body (into the board)
        n = (-n[0], -n[1])
    def pt(name, d, along=0.0):
        px, py = P[name]
        return (px + n[0] * d + u[0] * along, py + n[1] * d + u[1] * along)
    w = 0.25
    def T(net, a, b, layer=pcbnew.F_Cu, width=w):
        t = add_track(board, nets[net], a[0], a[1], b[0], b[1], width, layer); t.SetLocked(True)
    def Vv(net, a):
        v = add_via(board, nets[net], a[0], a[1]); v.SetLocked(True)
    # D- : B7 and A7 -> interior stubs + link (the A6 lane between them is free beyond the pad)
    dd = d_vbus - 0.4
    T('USB_D-', pt('B7', 0), pt('B7', 1.9)); T('USB_D-', pt('A7', 0), pt('A7', dd + 0.2)); T('USB_D-', pt('B7', 1.9), pt('A7', 1.9))
    # D+ : B6 -> interior stub -> via ; A6 -> under the body -> via ; inner/back diagonal joins them
    T('USB_D+', pt('B6', 0), pt('B6', dd - 0.6)); T('USB_D+', pt('B6', dd - 0.6), pt('B6', dd, 0.6)); Vv('USB_D+', pt('B6', dd, 0.6))
    T('USB_D+', pt('A6', 0), pt('A6', -1.9)); T('USB_D+', pt('A6', -1.9), pt('A6', -2.4, -0.5)); Vv('USB_D+', pt('A6', -2.4, -0.5))
    T('USB_D+', pt('A6', -2.4, -0.5), pt('B6', dd, 0.6), pcbnew.B_Cu)
    # VBUS : both pairs -> vias (pushed outwards along the row so the middle of the lane stays free), joined on B.Cu
    dv = d_vbus
    T('VBUS', pt('A4', 0), pt('A4', dv, -0.9), width=0.3); Vv('VBUS', pt('A4', dv, -0.9))
    T('VBUS', pt('B4', 0), pt('B4', dv, 0.9), width=0.3); Vv('VBUS', pt('B4', dv, 0.9))
    T('VBUS', pt('A4', dv, -0.9), pt('B4', dv, 0.9), pcbnew.B_Cu, 0.4)

def stitch_gnd(board, d, gnd, W, H):
    """Via next to every SMD GND pad + a sparse via grid, placed before autorouting so the router sees them."""
    obs = Obstacles(board, W, H)
    n_pad = 0; smd = []
    for fp in board.GetFootprints():
        # footprints that already own a through-hole GND pad (USB shell, module EP vias) reach the back pour by themselves
        if any(p.GetNetname() == 'GND' and p.GetAttribute() != pcbnew.PAD_ATTRIB_SMD for p in fp.Pads()):
            continue
        for pad in fp.Pads():
            if pad.GetNetname() == 'GND' and pad.GetAttribute() == pcbnew.PAD_ATTRIB_SMD:
                smd.append((pad, fp))
    for pad, fp in smd:
        if stitch_pad(board, obs, gnd, pad, fp):
            n_pad += 1
        else:
            print(f'  no stitch via for {fp.GetReference()} pad {pad.GetNumber()}')
    n_grid = 0
    for gx in range(5, int(W) - 3, 5):
        for gy in range(5, int(H) - 3, 5):
            if obs.via_ok(gx, gy, extra=2.0):
                add_via(board, gnd, gx, gy); obs.add_via(gx, gy); n_grid += 1
    print(f'GND stitching: {n_pad}/{len(smd)} SMD GND pads got a via, {n_grid} grid vias')

def build(out_path):
    d = design.build()
    W, H, R = d.board['w'], d.board['h'], d.board['corner']
    board = pcbnew.BOARD()
    board.SetFileName(out_path)
    layers = d.board.get('layers', 2)
    board.SetCopperLayerCount(layers)
    if layers == 4:
        board.SetLayerType(pcbnew.In1_Cu, pcbnew.LT_POWER)     # solid GND plane, not routed
        board.SetLayerType(pcbnew.In2_Cu, pcbnew.LT_SIGNAL)    # routing layer; GND pour fills the rest after routing
    # ---------------- design rules (JLCPCB 2-layer capability with margin) ----------------
    ds = board.GetDesignSettings()
    ds.m_TrackMinWidth = FromMM(d.board.get('min_width', 0.15)); ds.m_ViasMinSize = FromMM(0.5); ds.m_MinThroughDrill = FromMM(0.3)
    ds.m_MinClearance = FromMM(d.board.get('min_clearance', 0.127)); ds.m_CopperEdgeClearance = FromMM(0.3); ds.m_HoleClearance = FromMM(0.25)
    ds.m_MinSilkTextHeight = FromMM(0.8); ds.m_HoleToHoleMin = FromMM(0.5)
    ns = ds.m_NetSettings
    dflt = ns.GetDefaultNetclass()
    dflt.SetClearance(FromMM(0.15)); dflt.SetTrackWidth(FromMM(0.25)); dflt.SetViaDiameter(FromMM(0.7)); dflt.SetViaDrill(FromMM(0.3))
    pwr = pcbnew.NETCLASS('Power')
    pwr.SetClearance(FromMM(0.2)); pwr.SetTrackWidth(FromMM(0.4)); pwr.SetViaDiameter(FromMM(0.8)); pwr.SetViaDrill(FromMM(0.4))
    ns.SetNetclass('Power', pwr)
    for n in ['+5V', '+3V3', 'GND']:
        ns.SetNetclassPatternAssignment(n, 'Power')
    if hasattr(ds, 'm_MinResolvedSpokes'):
        ds.m_MinResolvedSpokes = 1
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
        board.Add(fp)
        fp.SetPosition(V(*p.pcb_pos))
        if p.side == 'bottom':
            fp.Flip(fp.GetPosition(), False)
        fp.SetOrientationDegrees(p.pcb_rot)
        if p.dnp:
            fp.SetDNP(True)
        fp.Value().SetVisible(False)
        if not d.silk_refs:
            fp.Reference().SetLayer(pcbnew.B_Fab if fp.IsFlipped() else pcbnew.F_Fab)
        if p.ref_pcb_pos:
            fp.Reference().SetPosition(V(*p.ref_pcb_pos[:2]))
            if len(p.ref_pcb_pos) > 2: fp.Reference().SetTextAngleDegrees(p.ref_pcb_pos[2])
        # make refs small
        fp.Reference().SetTextSize(VECTOR2I(FromMM(0.8), FromMM(0.8))); fp.Reference().SetTextThickness(FromMM(0.12))
        for pad in fp.Pads():
            net = p.pins.get(pad.GetNumber()) or p.extra_pads.get(pad.GetNumber())
            if net:
                pad.SetNet(nets[net])
            if p.drill and pad.GetDrillSize().x:
                pad.SetDrillSize(VECTOR2I(FromMM(p.drill), FromMM(p.drill)))
                pad.SetSize(VECTOR2I(FromMM(p.drill + 1.2), FromMM(p.drill + 1.2)))
            # JLCPCB: keep drills >= 0.3 mm (module thermal vias in the library are 0.2 mm)
            if pad.GetDrillSize().x and pad.GetDrillSize().x < FromMM(0.3):
                pad.SetDrillSize(VECTOR2I(FromMM(0.3), FromMM(0.3)))
                if pad.GetSize().x < FromMM(0.6):
                    pad.SetSize(VECTOR2I(FromMM(0.6), FromMM(0.6)))
        p._fp = fp
    # ---------------- outline ----------------
    outline(board, W, H, R)
    # ---------------- USB-C escape (hand-routed: the router cannot do the D+/D- pair swap at 0.5 mm pitch) ----------------
    preroute_usb(board, d.by_ref('J1')._fp, nets, W, d.board.get('usb_vbus_via', 5.4))
    for spec in d.via_in_pad:
        ref, num = spec.split(':')
        for pad in d.by_ref(ref)._fp.Pads():
            if pad.GetNumber() == num:
                add_via(board, nets[pad.GetNetname()], pad.GetPosition().x / 1e6, pad.GetPosition().y / 1e6, 0.6, 0.3)
    # ---------------- GND stitching (done before autorouting so the router sees the vias) ----------------
    stitch_gnd(board, d, nets['GND'], W, H)
    # ---------------- zones: GND pour both sides ----------------
    m = 0.5
    rect = [(m, m), (W - m, m), (W - m, H - m), (m, H - m)]
    add_zone(board, pcbnew.F_Cu, nets['GND'], rect, 'GND_F')
    add_zone(board, pcbnew.B_Cu, nets['GND'], rect, 'GND_B')
    for lname, net in d.board.get('inner_planes', {}).items():
        z = add_zone(board, board.GetLayerID(lname), nets[net], rect, 'PLANE_' + net)
        z.SetZoneName('plane'); z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    for lname in d.board.get('inner_pours', []):
        add_zone(board, board.GetLayerID(lname), nets['GND'], rect, 'GND_' + lname)
    # antenna keep-out: 15 mm around the module antenna, inside the board (antenna itself hangs off the top edge)
    u1 = d.by_ref('U1'); ux, uy = u1.pcb_pos
    for (x1, y1, x2, y2) in d.keepouts:
        add_zone(board, pcbnew.F_Cu, None, [(x1, y1), (x2, y1), (x2, y2), (x1, y2)], 'keepout', keepout=True)
    # ---------------- silkscreen ----------------
    for (txt, x, y, size, rot, layer, mirror) in d.silk:
        layer = {'F.SilkS': pcbnew.F_SilkS, 'B.SilkS': pcbnew.B_SilkS, 'F.Fab': pcbnew.F_Fab}[layer] if isinstance(layer, str) else layer
        add_text(board, txt, x, y, layer=layer, size=size, thick=max(0.12, size * 0.15), rot=rot, mirror=mirror)
    pcbnew.SaveBoard(out_path, board)
    return board, d

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'pcb', variant.BOARD + '.kicad_pcb')
    board, d = build(out)
    print('wrote', out, 'footprints', len(board.GetFootprints()), 'nets', board.GetNetCount())
    # report placement bounding boxes for sanity
    for p in d.parts:
        bb = p._fp.GetBoundingBox(False, False)
        print(f"{p.ref:4s} x[{bb.GetLeft()/1e6:6.2f},{bb.GetRight()/1e6:6.2f}] y[{bb.GetTop()/1e6:6.2f},{bb.GetBottom()/1e6:6.2f}]")
