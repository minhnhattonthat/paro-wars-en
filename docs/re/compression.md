# LZ compression

Routine: PAW.EXE `0x80013CB0(src, dst)`. **verified**: read breakpoint on the demo graphics buffer (`work/qa/d5`), disassembly, and `tests/test_lzkc.py`
(`decompress(compress(x)) == x` on real files). Decoded images look right in `work/recon/sweep/`. Codec: `tools/lzkc.py`.

```
u24 stream_len, u8 0, then stream_len bytes.  Output size is not stored.
window 1024 bytes, zero-filled, write position 0x3DE (window lives at RAM 0x801DE000)
flag byte, LSB first, refilled after 8 ops:
  0 -> one literal byte
  1 -> token t:
    t < 0x80   next byte b: copy (t>>2)+3 bytes from absolute window offset ((t&3)<<8)|b
    t < 0xC0   copy ((t>>4)&3)+2 bytes from write position - (t&0xF)
    t >= 0xC0  (t&0x3F)+8 literal bytes follow
stops when the read pointer passes the end
```

The game's copies run byte by byte through the window, so an overlapping source reads freshly written bytes; `compress()` mirrors that.
`lzkc.compress()` is a greedy encoder: it decodes correctly but is not byte-identical to Konami's output. So **only recompress files you changed**, and check that they still fit their sectors (`disc.md`). Its worst case is about 9/8 of the input.

## Where it is used
`tools/unpack_all.py` decodes whole files: 3,597 hit (BK_DT 3347, DEMO 166, ENDING 64, DATA 16, NYANTV 4); list in `work/recon/lz.tsv`. Its header test has false negatives by design and prints reason counts (no-header 691, too-small 1603, bad-stream 916).

Containers with an embedded stream (`tools/lz_embed.py`; offsets are per file, read them from the header, don't assume):
| Family | Stream at | Decodes to | State |
|---|---|---|---|
| `P_00`-`P_73`, `P_<name>` | P_08: +0x94, length field at the end of a u32 offset list | pixels, then the unit-info text page at +0x48xx | **verified** on P_08 |
| `S_<name>` | +0x200 | 0x4000 bytes, graphics | **guess**: first block of several |
| `ITEM.BIN` | +0x600 | 0x8830 bytes, graphics; the text is raw at +0 | **verified** by the sweep |
| `FLAG.BIN` | 32-byte palette, then 9 streams back to back at +0x20, +0x884, +0xEE9, +0x163D, +0x1F3D, +0x26FA, +0x2D4F, +0x357D, +0x3A9C (not aligned; each ends where its length says) | 0x2000 bytes each: name strips over a flag, 8 nations and ニャー帝国. The turn banner, decoded to 0x150000 | **verified** by a write trace (decoder 0x80013D64) |
| `BATTLE0-5`, `BK_DT/*` | +0 | backdrops | **verified** |

Noise warning: `lz_embed.py` prints many short false hits. Trust a hit only when the stream reaches the end of the file or the next offset in the header, and the output looks like data.
