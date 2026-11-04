-- Log every text-engine glyph load: the font context pointers, glyph code and font cell.
-- emu.py ... --debugger --script tools/debug/glyphs.lua (0x8006725c is PAW.EXE's load-glyph routine, docs/re/text.md)
local mem = PCSX.getMemPtr()
local ffi = require("ffi")
local function rd32(addr)
  return ffi.cast("uint32_t*", mem + bit.band(addr, 0x1FFFFF))[0]
end
local function rd16(addr)
  return ffi.cast("uint16_t*", mem + bit.band(addr, 0x1FFFFF))[0]
end
local count = 0
L.on_exec(0x8006725C, function()
  local r = PCSX.getRegisters().GPR.n
  local a0 = tonumber(r.a0)
  count = count + 1
  if count <= 40 then
    L.log(string.format("f%d ctx=%08X cell=%d code=%04X a3=%d font=%08X tex=%08X ra=%08X",
      L.frame, a0, tonumber(r.a1), rd16(tonumber(r.a2)), tonumber(r.a3), rd32(a0 + 0x14EC), rd32(a0 + 0x14E4), tonumber(r.ra)))
  end
end)
