import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import design
from gen_sch import write_schematic
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
d = design.build()
out = os.path.join(ROOT, 'pcb', 'pl60c_dmx.kicad_sch')
write_schematic(d, out, 'pl60c_dmx')
print('wrote', out)
