-- Cold-boot warp: reach a scene from tools/debug/scenes.tsv by name (docs/re/flow.md has the state variables).
-- emu.py ROM.cue --out D --script tools/debug/warp.lua --var "SCENE='story_pen_0'" --frames 60000
-- Finishes by itself with D/<scene>.png; exit 2 if the scene was not reached.
local ffi = require("ffi")
local mem = PCSX.getMemPtr()
local function a(x) return bit.band(x, 0x1FFFFF) end
local function r8(x) return tonumber(ffi.cast("uint8_t*", mem + a(x))[0]) end
local function r16(x) return tonumber(ffi.cast("int16_t*", mem + a(x))[0]) end
local function r32(x) return tonumber(ffi.cast("uint32_t*", mem + a(x))[0]) end
local function w8(x, v) ffi.cast("uint8_t*", mem + a(x))[0] = v end
local function w16(x, v) ffi.cast("uint16_t*", mem + a(x))[0] = v end
local function w32(x, v) ffi.cast("uint32_t*", mem + a(x))[0] = v end

local CTX, G = 0x800C44E0, 0x800E0178
local function mode() return r32(CTX + 0x1548) end
local function sub() return r32(CTX + 0x1550) end
local function mapstate() return r32(0x800C5A30) end
local COUNTRY = { pen = 0, but = 1, tak = 2, lov = 3, ait = 4, moa = 5, pan = 6, bau = 7 }

-- scenes.tsv sits above --out in the repo, and the emulator's cwd is its own folder.
local function load_scenes()
  local dir = OUT:gsub("\\", "/")
  while dir:find("/") do
    dir = dir:gsub("/[^/]*$", "")
    local f = io.open(dir .. "/tools/debug/scenes.tsv", "r")
    if f then
      local rows = {}
      for line in f:lines() do
        if line ~= "" and line:sub(1, 1) ~= "#" then
          local c = {}
          for x in (line .. "\t"):gmatch("(.-)\t") do c[#c + 1] = x end
          rows[c[1]] = c
        end
      end
      f:close()
      return rows
    end
  end
  error("scenes.tsv not found above " .. OUT)
end

-- Coroutine helpers: each yield is one frame.
local function frames(n) for _ = 1, n do coroutine.yield() end end
local function wait(cond, limit, what)
  for _ = 1, limit or 20000 do
    if cond() then return end
    coroutine.yield()
  end
  error("timeout waiting for " .. (what or "condition") .. string.format(" mode=%d sub=%d", mode(), sub()))
end
local function tap(key, gap)
  L.press(key, 6)
  frames(6)
  frames(gap or 40)
end
local function mash(key, cond, gap, limit, what)
  local t = 0
  while not cond() do
    tap(key, gap)
    t = t + 1
    if t > (limit or 500) then error("mash timeout: " .. (what or "?")) end
  end
end

-- Title: start skips the intro and enables the menu, start again confirms NEW GAME (boot EXE passes 0 at 0x80010000).
local function to_select()
  mash("start", function() return r32(0x8014B000) == 0xC end, 94, 200, "PAW.EXE load")
  wait(function() return mode() == 2 and sub() >= 2 end, 3000, "SELECT")
end
-- Default cursors: scenario mode, default level, first country. Ends on the first frame of mode 3.
local function to_story()
  to_select()
  mash("circle", function() return mode() == 3 end, 54, 200, "story mode")
end

local function story(c, ch)
  to_story()
  w8(G + 0x154, c)
  w8(G + 0xD02, ch)
  wait(function() return mode() == 3 and sub() == 3 end, 3000, "story pages")
  -- MAP_DEMO's table of TXT_* records: row country, column chapter, {ram, size, lba}.
  L.log(string.format("story text lba %d", r32(0x8018DE5C + (c * 8 + ch) * 12 + 8)))
  for _ = 1, 10 do tap("circle", 54) end
end

-- Start skips the story pages (MAP_DEMO 0x80188638); then GAME_OV shows the mission card and the map.
local function to_mission(c, ch)
  to_story()
  w8(G + 0x154, c)
  w8(G + 0xD02, ch)
  wait(function() return mode() == 3 and sub() == 3 end, 3000, "story pages")
  frames(30)
  mash("start", function() return mode() == 4 end, 54, 40, "mission")
end

-- Units are a linked list from 0x80133304 (+4 next, +8 commander, +0xC type record, +0x14 x, +0x15 y). Side = commander block index.
local function units()
  local u = 0x80133304
  return function()
    if u == 0 then return nil end
    local cur = u
    u = r32(u + 4)
    return cur
  end
end
local function unit_side(u) return bit.rshift(r32(u + 8) - 0x800F9620, 10) end

-- Space-separated steps: a button name (6-frame press, 40-frame gap), wN (wait N frames), s (shot x<frame>.png),
-- "down+circle" for chords. Used by scene rows and by the EXPLORE global for one-off RE runs.
local function steps(str)
  -- 40*[circle w100 s] repeats its contents
  str = (str or ""):gsub("(%d+)%*%[(.-)%]", function(n, body) return string.rep(body .. " ", tonumber(n)) end)
  for tok in str:gmatch("%S+") do
    local off, val = tok:match("^g(0x%x+)=(%d+)$")  -- g0x798=2: poke a byte of the game block at 0x800E0178
    local wm, ws = tok:match("^until(%d+)%.(%d+)$")  -- until4.9: wait for mode 4 sub 9
    local abs, aval = tok:match("^m(0x%x+)=(%d+)$")  -- m0x80133364=10: poke any RAM byte
    if off then w8(G + tonumber(off), tonumber(val))
    elseif abs then w8(tonumber(abs), tonumber(aval))
    elseif tok == "units" then
      for u in units() do
        L.log(string.format("unit %08X side=%d type=%08X x=%d y=%d", u, unit_side(u), r32(u + 0xC), r8(u + 0x14), r8(u + 0x15)))
      end
    elseif tok:match("^state=%d+$") then  -- force the map sub-state (table 0x800A2FC8), which requests its overlay
      w16(G + 0x18, tonumber(tok:match("%d+")))
      w16(G + 0x1C, 0)
      w16(G + 0x20, 0)
    elseif tok == "until-attack" then wait(function() return mode() == 4 and r16(G + 0x18) == 2 end, 30000, tok)
    elseif tok == "dump" then L.dump_ram(string.format("d%06d.bin", L.frame))
    elseif wm then
      local m, n = tonumber(wm), tonumber(ws)
      wait(function() return mode() == m and sub() == n end, 8000, tok)
    elseif tok == "s" then L.shot(string.format("x%06d.png", L.frame))
    elseif tok:match("^w%d+$") then frames(tonumber(tok:sub(2)))
    else tap(tok, 40) end
  end
end

local KIND = {
  story = function(row) story(COUNTRY[row[3]], tonumber(row[4])) end,
  -- Circle at the title (start is what opens the menu): the boot EXE passes 1 at 0x80010000 and PAW plays an AI demo (modes 1, 4).
  attract = function(row)
    mash("circle", function() return mode() == 4 and sub() == 8 end, 54, 400, "attract demo")
    steps(row[3])
    steps(EXPLORE)
  end,
  -- The mission title card: mode 4 sub 7 runs about 240 frames, the card fills the middle of it.
  card = function(row)
    to_mission(COUNTRY[row[3]], tonumber(row[4]))
    wait(function() return mode() == 4 and sub() == 7 end, 2000, "card")
    frames(120)
    L.log(string.format("map %d chapter %d country %d", r8(G + 6), r8(G + 0xD02), r8(G + 0x154)))
  end,
  -- ending country last_chapter [steps]: win the last chapter; BEND_OV sees G+6 == 9 and sets mode 5 (ENDING.BIN).
  ending = function(row)
    to_mission(COUNTRY[row[3]], tonumber(row[4]))
    wait(function() return mode() == 4 and sub() == 8 end, 2000, "map")
    frames(120)
    w8(G + 0x798, 2)
    wait(function() return mode() == 5 end, 3000, "ending")
    steps(row[5])
    steps(EXPLORE)
  end,
  -- mapbattle [steps]: second item on the mode select.
  mapbattle = function(row)
    to_select()
    frames(300)  -- the mode list ignores presses while it slides in
    tap("right", 60)  -- the two modes sit side by side
    L.shot(string.format("x%06d.png", L.frame))
    tap("circle", 120)
    steps(row[3])
    steps(EXPLORE)
  end,
  -- mission country chapter [steps]: from the mission's map, after the "explain?" prompt appears.
  mission = function(row)
    to_mission(COUNTRY[row[3]], tonumber(row[4]))
    wait(function() return mode() == 4 and sub() >= 8 end, 2000, "map")
    steps(row[5])
    steps(EXPLORE)
  end,
}

SCENE = SCENE or "story_pen_0"
local row = load_scenes()[SCENE] or error("unknown scene " .. SCENE)
local co = coroutine.create(function()
  KIND[row[2]](row)
  L.shot(SCENE .. ".png")
  L.log(string.format("reached %s frame %d mode=%d sub=%d", SCENE, L.frame, mode(), sub()))
  if STATE_OUT then L.save_state(STATE_OUT) end  -- the driver only saves when --frames runs out, and we finish early
  L.finish(0)
end)
L.on_frame(function()
  local ok, e = coroutine.resume(co)
  if not ok then L.fail(debug.traceback(co, e)) end
end)
