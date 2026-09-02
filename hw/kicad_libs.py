"""Load KiCad symbols (with `extends` flattening) from the bundled libraries."""
import os, copy
from sexp import parse, find, findall, Sym

KICAD_SHARE = "/Applications/KiCad/KiCad.app/Contents/SharedSupport"
SYM_DIR = os.path.join(KICAD_SHARE, "symbols")
FP_DIR = os.path.join(KICAD_SHARE, "footprints")

_lib_cache = {}

def _load_lib(libname):
    if libname not in _lib_cache:
        with open(os.path.join(SYM_DIR, libname + ".kicad_sym")) as f:
            tree = parse(f.read())[0]
        d = {}
        for s in findall(tree, 'symbol'):
            d[s[1]] = s
        _lib_cache[libname] = d
    return _lib_cache[libname]

def get_symbol(lib_id):
    """Return a flattened copy of symbol `Lib:Name` with lib_id-prefixed names."""
    libname, name = lib_id.split(':', 1)
    lib = _load_lib(libname)
    sym = copy.deepcopy(lib[name])
    ext = find(sym, 'extends')
    if ext:
        parent = copy.deepcopy(lib[ext[1]])
        # child properties override parent's; drawing units come from parent
        child_props = {p[1]: p for p in findall(sym, 'property')}
        merged = [Sym('symbol'), name]
        for x in parent[2:]:
            if isinstance(x, list) and x[0] == 'property':
                merged.append(child_props.pop(x[1], x))
            elif isinstance(x, list) and x[0] == 'symbol':
                # rename sub-units parent_1_1 -> name_1_1
                x = copy.deepcopy(x)
                x[1] = name + x[1][len(ext[1]):]
                merged.append(x)
            elif isinstance(x, list) and x[0] == 'extends':
                continue
            else:
                merged.append(x)
        for p in child_props.values():
            merged.append(p)
        sym = merged
    # prefix names with lib
    sym[1] = lib_id
    for x in sym:
        if isinstance(x, list) and x[0] == 'symbol':
            x[1] = libname + ':' + x[1]
    return sym

def symbol_pins(sym):
    """List of dicts: number, name, x, y, angle, length, type (for unit 1 / common units)."""
    pins = []
    for sub in findall(sym, 'symbol'):
        for p in findall(sub, 'pin'):
            at = find(p, 'at'); num = find(p, 'number'); nm = find(p, 'name'); ln = find(p, 'length')
            pins.append(dict(number=str(num[1]), name=str(nm[1]), x=float(at[1]), y=float(at[2]),
                             angle=float(at[3]) if len(at) > 3 else 0.0, length=float(ln[1]) if ln else 2.54,
                             type=str(p[1]), unit=sub[1]))
    return pins

def footprint_path(fp_id):
    lib, name = fp_id.split(':', 1)
    return os.path.join(FP_DIR, lib + '.pretty'), name
