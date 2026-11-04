-- Log each distinct text window drawn: position, wrap column, line gap, code count, flags, lines, widest line in px, and the text's first letters.
-- The width gate reads these (docs/re/boxes.md). emu.py ... --script tools/debug/warp.lua --script tools/debug/boxes.lua
local ffi = require("ffi")
local mem = PCSX.getMemPtr()
local function a(x) return bit.band(x, 0x1FFFFF) end
local function r8(x) return tonumber(ffi.cast("uint8_t*", mem + a(x))[0]) end
local function r16(x) return tonumber(ffi.cast("uint16_t*", mem + a(x))[0]) end
local function s16(x) return tonumber(ffi.cast("int16_t*", mem + a(x))[0]) end
local function r32(x) return tonumber(ffi.cast("uint32_t*", mem + a(x))[0]) end
local CTX = 0x800C44E0
local WIDTHS = 0x80067C8C  -- asm/vwf.asm
local seen, peak = {}, 0

-- Pixels and lines of a window's text, and its first letters. Fullwidth codes count 12 and stand as ? in the head.
local function measure(p, count, wrap)
  local widest, pen, lines, head = 0, 0, 1, {}
  local function brk()
    if pen > widest then widest = pen end
    pen = 0
    lines = lines + 1
  end
  local function letter(b)
    if b == 0x0A then brk()
    elseif b ~= 0x1F and b >= 0x20 and b < 0x80 then
      pen = pen + r8(WIDTHS + b - 0x20)
      if #head < 12 then head[#head + 1] = string.char(b == 0x7F and 0x2A or b) end
    end
  end
  for i = 0, count - 1 do
    local code = r16(p + i * 2)
    if bit.rshift(code, 8) == 0x1E then
      pen = bit.band(code, 0xFF) * 2
    elseif code < 0x8000 then
      letter(bit.rshift(code, 8))
      letter(bit.band(code, 0xFF))
    else
      if code == 0x8197 then brk() else pen = pen + 12 end
      if #head < 12 then head[#head + 1] = "?" end
    end
  end
  if pen > widest then widest = pen end
  return widest, lines, table.concat(head)
end

L.on_frame(function()
  -- All 0x60 slots, not the active list: one-frame windows are off the list again by vblank, but their slot still holds them.
  for i = 0, 0x5F do
    local w = CTX + 0x680 + i * 28
    local p, count = r32(w + 0x14), r16(w + 0xE)
    if math.floor(p / 0x1000000) == 0x80 and count > 0 and count < 400 then
      local x, y, wrap, gap, flags = s16(w + 4), s16(w + 6), r8(w + 8), r8(w + 0x19), r8(w + 0x18)
      local px, lines, head = measure(p, count, wrap)
      local key = string.format("%x %d %d %d %d %d %s", p, x, y, wrap, gap, count, head)
      if not seen[key] then
        seen[key] = true
        local codes = {}
        for k = 0, math.min(count, 16) - 1 do codes[#codes + 1] = string.format("%04x", r16(p + k * 2)) end
        L.log(string.format("BOX f%d x=%d y=%d wrap=%d gap=%d count=%d flags=%x type=%d px=%d lines=%d ptr=%08x codes=%s head=%s",
          L.frame, x, y, wrap, gap, count, flags, r8(w), px, lines, p, table.concat(codes), head))
      end
    end
  end
  local mode, sub = r32(CTX + 0x1548), r32(CTX + 0x1550)
  local buf = r32(CTX + 0x1560)
  local top = r32(CTX + 0x1660)
  local used = top - (0x800C64F8 + buf * 0xCE40)
  if mode == 4 and sub == 8 then used = 0 end  -- the map state gives text its own pool
  if used > peak and used < 0x20000 then
    peak = used
    L.log(string.format("POOL f%d used=%d of 52800", L.frame, used))
  end
end)
