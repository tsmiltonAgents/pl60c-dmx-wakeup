"""Generate a KiCad schematic (.kicad_sch) from a Design object (see design.py)."""
import math
from sexp import Sym, dumps, new_uuid, find
from kicad_libs import get_symbol, symbol_pins

S = Sym
POWER_NETS = {'GND': 'power:GND', '+3V3': 'power:+3V3', '+5V': 'power:+5V'}

def _font(size=1.27, hide=False, justify=None):
    e = [S('effects'), [S('font'), [S('size'), size, size]]]
    if justify: e.append([S('justify')] + [S(j) for j in justify.split()])
    if hide: e.append([S('hide'), S('yes')])
    return e

def _prop(name, val, x, y, rot=0, hide=False, justify=None):
    return [S('property'), name, val, [S('at'), x, y, rot], _font(hide=hide, justify=justify)]

def _rot(px, py, rot):
    r = math.radians(rot); c, s = round(math.cos(r)), round(math.sin(r))
    return px * c - py * s, px * s + py * c

def pin_world(part, pin):
    """Schematic (y-down) coords of a pin's connection point + outward direction (0=right,90=up,180=left,270=down)."""
    dx, dy = _rot(pin['x'], pin['y'], part.sch_rot)
    x = part.sch_pos[0] + dx
    y = part.sch_pos[1] - dy
    outward = (pin['angle'] + 180 + part.sch_rot) % 360
    return round(x, 4), round(y, 4), outward

def _dir_vec(angle):
    return {0: (1, 0), 90: (0, -1), 180: (-1, 0), 270: (0, 1)}[int(angle) % 360]

def _sym_instance(part, pins, proj_name, root_uuid):
    x, y = part.sch_pos
    inst = [S('symbol'), [S('lib_id'), part.lib_id], [S('at'), x, y, part.sch_rot], [S('unit'), 1],
            [S('exclude_from_sim'), S('no')], [S('in_bom'), S('yes')],
            [S('on_board'), S('yes')], [S('dnp'), S('yes' if part.dnp else 'no')], [S('uuid'), part.uuid]]
    ys = [p['y'] for p in pins] or [0]
    top = y - max(ys) - 2.54
    bot = y - min(ys) + 2.54
    rx, ry = part.ref_pos if part.ref_pos else (x, top - 1.27)
    vx, vy = part.val_pos if part.val_pos else (x, bot + 1.27)
    inst.append(_prop('Reference', part.ref, rx, ry))
    inst.append(_prop('Value', part.value, vx, vy))
    inst.append(_prop('Footprint', part.footprint, x, y, hide=True))
    inst.append(_prop('Datasheet', part.datasheet or '~', x, y, hide=True))
    inst.append(_prop('Description', part.desc or '', x, y, hide=True))
    inst.append(_prop('LCSC', part.lcsc or '', x, y, hide=True))
    if part.mpn: inst.append(_prop('MPN', part.mpn, x, y, hide=True))
    seen = set()
    for p in pins:
        if p['number'] in seen: continue
        seen.add(p['number'])
        inst.append([S('pin'), p['number'], [S('uuid'), new_uuid()]])
    inst.append([S('instances'), [S('project'), proj_name, [S('path'), '/' + root_uuid, [S('reference'), part.ref], [S('unit'), 1]]]])
    return inst

def _wire(x1, y1, x2, y2):
    return [S('wire'), [S('pts'), [S('xy'), x1, y1], [S('xy'), x2, y2]], [S('stroke'), [S('width'), 0], [S('type'), S('default')]], [S('uuid'), new_uuid()]]

def _label(name, x, y, outward):
    just = {0: 'left bottom', 180: 'right bottom', 90: 'left bottom', 270: 'right bottom'}[outward]
    return [S('label'), name, [S('at'), x, y, outward], [S('fields_autoplaced'), S('yes')], _font(justify=just), [S('uuid'), new_uuid()]]

def _no_connect(x, y):
    return [S('no_connect'), [S('at'), x, y], [S('uuid'), new_uuid()]]

def _text(txt, x, y, size=1.27, bold=False):
    font = [S('font'), [S('size'), size, size]]
    if bold: font.append([S('bold'), S('yes')])
    e = [S('effects'), font, [S('justify'), S('left'), S('bottom')]]
    return [S('text'), txt, [S('exclude_from_sim'), S('no')], [S('at'), x, y, 0], e, [S('uuid'), new_uuid()]]

def _rect(x1, y1, x2, y2):
    return [S('rectangle'), [S('start'), x1, y1], [S('end'), x2, y2],
            [S('stroke'), [S('width'), 0.15], [S('type'), S('dash')]], [S('fill'), [S('type'), S('none')]], [S('uuid'), new_uuid()]]

def _generic_instance(lib_id, ref, value, x, y, rot, proj_name, root_uuid, val_pos, hide_value=False):
    inst = [S('symbol'), [S('lib_id'), lib_id], [S('at'), x, y, rot], [S('unit'), 1],
            [S('exclude_from_sim'), S('no')], [S('in_bom'), S('yes')], [S('on_board'), S('yes')], [S('dnp'), S('no')],
            [S('uuid'), new_uuid()],
            _prop('Reference', ref, x, y, hide=True), _prop('Value', value, val_pos[0], val_pos[1], hide=hide_value),
            _prop('Footprint', '', x, y, hide=True), _prop('Datasheet', '', x, y, hide=True), _prop('Description', '', x, y, hide=True),
            [S('pin'), '1', [S('uuid'), new_uuid()]],
            [S('instances'), [S('project'), proj_name, [S('path'), '/' + root_uuid, [S('reference'), ref], [S('unit'), 1]]]]]
    return inst

def _power_symbol(net, x, y, outward, ref, proj_name, root_uuid, cache):
    """Power symbol whose pin sits at (x,y); graphic extends in direction `outward`."""
    lib_id = POWER_NETS[net]
    cache.setdefault(lib_id, get_symbol(lib_id))
    # power:GND pin angle 270 => graphic below pin when rot=0. rails: pin angle 90 => graphic above when rot=0.
    if net == 'GND':
        rot = {270: 0, 0: 270, 90: 180, 180: 90}[outward]
    else:
        rot = {90: 0, 180: 270, 270: 180, 0: 90}[outward]
    vx, vy = _dir_vec(outward)
    val_pos = (x + vx * 4.5, y + vy * 4.5 + (1.0 if outward == 270 else 0))
    return _generic_instance(lib_id, ref, net, x, y, rot, proj_name, root_uuid, val_pos)

def write_schematic(design, path, proj_name):
    root_uuid = design.sch_uuid
    lib_cache = {}
    items = []
    pwr_n = 0
    for part in design.parts:
        part.sch_pos = (round(round(part.sch_pos[0] / 1.27) * 1.27, 4), round(round(part.sch_pos[1] / 1.27) * 1.27, 4))
        sym = lib_cache.setdefault(part.lib_id, get_symbol(part.lib_id))
        pins = symbol_pins(sym)
        part._pins = pins
        items.append(_sym_instance(part, pins, proj_name, root_uuid))
        done_pos = set()
        for p in pins:
            x, y, outward = pin_world(part, p)
            if (x, y) in done_pos:
                continue  # stacked pins share one connection point
            done_pos.add((x, y))
            net = part.pins.get(p['number'], None)
            if net is None:
                items.append(_no_connect(x, y))
                continue
            vx, vy = _dir_vec(outward)
            stub = part.stub
            x2, y2 = round(x + vx * stub, 4), round(y + vy * stub, 4)
            items.append(_wire(x, y, x2, y2))
            use_pwr = net in POWER_NETS and ((net == 'GND' and outward == 270) or (net != 'GND' and outward == 90) or part.power_symbols_any)
            if use_pwr:
                pwr_n += 1
                items.append(_power_symbol(net, x2, y2, outward, f'#PWR{pwr_n:03d}', proj_name, root_uuid, lib_cache))
            else:
                items.append(_label(net, x2, y2, outward))
    # Power flags
    lib_cache.setdefault('power:PWR_FLAG', get_symbol('power:PWR_FLAG'))
    for net, (x, y) in design.pwr_flags.items():
        x, y = round(round(x / 1.27) * 1.27, 4), round(round(y / 1.27) * 1.27, 4)
        pwr_n += 1
        outward = 270 if net == 'GND' else 90
        vx, vy = _dir_vec(outward)
        items.append(_wire(x, y, x + vx * 2.54, y + vy * 2.54))
        items.append(_power_symbol(net, x + vx * 2.54, y + vy * 2.54, outward, f'#PWR{pwr_n:03d}', proj_name, root_uuid, lib_cache))
        pwr_n += 1
        items.append(_generic_instance('power:PWR_FLAG', f'#FLG{pwr_n:03d}', 'PWR_FLAG', x, y, 0, proj_name, root_uuid, (x, y - 3.8)))
    for (txt, x, y, size, bold) in design.texts:
        items.append(_text(txt, x, y, size, bold))
    for (x1, y1, x2, y2) in design.boxes:
        items.append(_rect(x1, y1, x2, y2))
    lib_symbols = [S('lib_symbols')] + [lib_cache[k] for k in sorted(lib_cache)]
    doc = [S('kicad_sch'), [S("version"), 20260306], [S("generator"), "eeschema"], [S("generator_version"), "10.0"],
           [S('uuid'), root_uuid], [S('paper'), design.paper],
           [S('title_block'), [S('title'), design.title], [S('date'), design.date], [S('rev'), design.rev], [S('company'), design.company]],
           lib_symbols] + items + [[S('sheet_instances'), [S('path'), '/', [S('page'), '1']]], [S('embedded_fonts'), S('no')]]
    with open(path, 'w') as f:
        f.write(dumps(doc) + '\n')
