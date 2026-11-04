#!/bin/sh
# One-off RE run: x.sh NAME SCENE "STEPS" [FRAMES] -> work/qa/x/NAME/{log.txt,sheet.png}. Steps as in warp.lua; adds the state trace.
cd "$(dirname "$0")/../.." || exit 1
S=$(python tools/skill.py)
o=work/qa/x/$1
rm -rf "$o"; mkdir -p "$o"
python -X utf8 "$S/scripts/emu.py" "${ROM:-rom/Paro Wars (Japan).cue}" --out "$o" --script tools/debug/warp.lua --var "SCENE='$2'" --var "EXPLORE='$3'" --script tools/debug/trace.lua --frames "${4:-30000}" --timeout 500 > "$o/run.txt" 2>&1
echo "exit $?"
tail -n 12 "$o/log.txt"
python -X utf8 "$S/scripts/sheet.py" "$o/x*.png" --cols 6 --div 2 --max 36 --out "$o/sheet.png" 2>&1 | tail -n 2
