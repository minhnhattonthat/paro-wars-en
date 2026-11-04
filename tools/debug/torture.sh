#!/bin/sh
# Glyph torture and ruler pages on the first story chapter: build/paro_wars_torture.cue, shots in work/qa/torture.
# Page 1: every printable letter, double spaces, the ellipsis, Greek, a tab. Page 2: a ruler, to read the box's last column off the pixels. Page 3: a line of the widest letter.
cd "$(dirname "$0")/../.." || exit 1
S=$(python tools/skill.py)
RULER='012345678901234567890123456789012345678901234567890'
python -X utf8 tools/build.py --out paro_wars_torture \
  --qa 'DEMO/TXT_PEN0:96=!"#$%&'"'"'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ{br}[\]^_`abcdefghijklmnopqrstuvwxyz{|}~  two  spaces{br}…κξαδμ{x:200}tab at 200' \
  --qa "DEMO/TXT_PEN0:12c=$RULER{br}iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii{br}third line, whose end sits beside the page arrow, 1234567" \
  --qa 'DEMO/TXT_PEN0:1c2=MMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMMM{br}WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW{br}gjpqy gjpqy descenders on the last line, gjpqy' || exit 1
o=work/qa/torture
rm -rf "$o"; mkdir -p "$o"
python -X utf8 "$S/scripts/emu.py" build/paro_wars_torture.cue --out "$o" --script tools/debug/warp.lua --var "SCENE='story_pages'" --frames 60000 --timeout 500 > "$o/run.txt" 2>&1
tail -n 2 "$o/run.txt"
python -X utf8 "$S/scripts/sheet.py" "$o/x*.png" --cols 2 --out "$o/sheet.png" | tail -n 1
