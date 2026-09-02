import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import variant
design = variant.design()
from gen_sch import write_schematic
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = design.build()
out = os.path.join(ROOT, 'pcb', variant.BOARD + '.kicad_sch')
write_schematic(d, out, variant.BOARD)
print('wrote', out)
