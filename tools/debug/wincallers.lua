-- Log each distinct caller of the window creators (docs/re/font.md): creator, return address, x, y, text and its first bytes.
-- emu.py ... --debugger --script tools/debug/warp.lua --script tools/debug/wincallers.lua: finds code that places a label by its count.
local ffi = require("ffi")
local mem = PCSX.getMemPtr()
local function r8(a) return ffi.cast("uint8_t*", mem + bit.band(a, 0x1FFFFF))[0] end
local seen = {}
local function hook(addr)
  L.on_exec(addr, function()
    local r = PCSX.getRegisters().GPR.n
    local key = string.format("%x %x %x", addr, r.ra, r.a3)
    if seen[key] then return end
    seen[key] = true
    local head = {}
    if bit.rshift(r.a3, 24) == 0x80 then for i = 0, 11 do head[#head + 1] = string.format("%02x", r8(r.a3 + i)) end end
    L.log(string.format("WIN f%d fn=%x ra=%x x=%d y=%d text=%x %s", L.frame, addr, r.ra, r.a1, r.a2, r.a3, table.concat(head)))
  end)
end
for _, a in ipairs({ 0x80068270, 0x8006837C, 0x80068748, 0x80068838 }) do hook(a) end
