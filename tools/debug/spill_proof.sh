#!/bin/sh
# Proves build.py's spill in game: incompressible pages push LOV_TXT past its one sector, so it must load from a disc gap. -> work/qa/x/spill
cd "$(dirname "$0")/../.." || exit 1
ids="1194 122a 12c0 1356 13ec 1482 1518 15ae 1644 16da 1770 1806"
args=""
i=0
for id in $ids; do
  i=$((i + 1))
  args="$args --qa ENDING/LOV_TXT:$id=Spill$i-$(python -c "import random,string;random.seed($i);print(''.join(random.choices(string.ascii_letters,k=120)))")"
done
python -X utf8 tools/build.py --out paro_wars_spill $args || exit 1
ROM=build/paro_wars_spill.cue sh tools/debug/x.sh spill ending_lov "12*[circle w240 s]" 40000
