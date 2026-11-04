-- Log every change of the game's state variables (docs/re/flow.md), with a shot per change when TRACE_SHOTS is set.
-- emu.py ... --script tools/debug/trace.lua [--var TRACE_SHOTS=1]
local ffi = require("ffi")
local mem = PCSX.getMemPtr()
local function r32(a) return ffi.cast("uint32_t*", mem + bit.band(a, 0x1FFFFF))[0] end
local function r16(a) return ffi.cast("int16_t*", mem + bit.band(a, 0x1FFFFF))[0] end
local CTX = 0x800C44E0
local VARS = {
  { "mode", function() return r32(CTX + 0x1548) end },
  { "sub", function() return r32(CTX + 0x1550) end },
  { "busy", function() return r16(CTX + 0x3AE) end },
  { "task0", function() return r16(CTX + 0x3B0) end },
  { "task1", function() return r16(CTX + 0x3B2) end },
  { "ov14b", function() return r32(0x8014B000) end },
  { "ov188", function() return r32(0x80188000) end },
  { "ov155", function() return r32(0x80155800) end },  -- second overlay slot (table 0x80010860)
  { "ov15c", function() return r32(0x8015C800) end },
  { "ov15e", function() return r32(0x8015E400) end },
  { "g18", function() return r16(0x800E0190) end },
}
for _, v in ipairs(TRACE_EXTRA or {}) do
  local a = v[2]
  VARS[#VARS + 1] = { v[1], v[3] == 16 and function() return r16(a) end or function() return r32(a) end }
end
local last = {}
L.on_frame(function(n)
  local changed, s = false, {}
  for _, v in ipairs(VARS) do
    local x = tonumber(v[2]())
    if x ~= last[v[1]] then changed = true end
    last[v[1]] = x
    s[#s + 1] = string.format("%s=%x", v[1], x)
  end
  if changed then
    L.log(string.format("f%d %s", n, table.concat(s, " ")))
    if TRACE_SHOTS then L.shot(string.format("t%06d.png", n)) end
  end
end)
