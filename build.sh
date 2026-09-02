#!/bin/bash
# Full reproducible build: schematic -> ERC -> PCB -> autoroute (retry until clean) -> DRC -> production files.
set -e -o pipefail
cd "$(dirname "$0")"
export PL60C_VARIANT=${1:-a}
B=pl60c_dmx; [ "$PL60C_VARIANT" != a ] && B=pl60c_dmx_$PL60C_VARIANT
echo "variant: $PL60C_VARIANT ($B)"
KP=/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3
KC=/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli
Q='grep -v "Fontconfig\|Debug:\|assert\|wxApp\|swig"'
filt() { grep -v "Fontconfig\|Debug:\|assert\|wxApp\|swig" || true; }
mkdir -p build
echo "== schematic"; python3 hw/build_sch.py | filt
$KC sch erc --output build/erc_$B.rpt --severity-all --exit-code-violations pcb/$B.kicad_sch 2>&1 | filt | tail -1 || true
echo "   ERC: $(grep -c '^\[' build/erc_$B.rpt || true) findings"; grep '^\[' build/erc_$B.rpt | sort | uniq -c || true
echo "== netlist check"; $KC sch export netlist --format kicadsexpr --output build/sch_$B.net pcb/$B.kicad_sch 2>&1 | filt | tail -0
python3 tools/verify_netlist.py
for attempt in 1 2 3 4 5 6; do
  echo "== pcb (attempt $attempt)"; $KP hw/gen_pcb.py 2>&1 | filt | head -1
  ($KP hw/route.py pcb/$B.kicad_pcb 150 2>&1 || true) | filt | tail -1
  ($KP hw/fix_gnd.py pcb/$B.kicad_pcb 2>&1 || true) | filt | tail -1
  ($KC pcb drc --output build/drc_$B.rpt --severity-all pcb/$B.kicad_pcb 2>&1 || true) | filt | tail -1
  ERR=$(grep -c "; error" build/drc_$B.rpt || true)
  echo "   DRC errors: $ERR"; grep '^\[' build/drc_$B.rpt | sort | uniq -c
  if [ "$ERR" = "0" ]; then break; fi
done
[ "$ERR" = "0" ] || { echo "DRC still has errors after retries"; exit 1; }
echo "== pcb vs schematic netlist"; $KP tools/verify_pcb.py 2>&1 | filt
echo "== production files"; $KP tools/export.py 2>&1 | filt | tail -12
echo "== done"
