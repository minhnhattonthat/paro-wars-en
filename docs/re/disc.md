# Disc layout

Single MODE2/2352 data track, 702,250,752 bytes, 6,885 ISO files. Serial SLPM-86016. Unpacks with dumpsxiso 2.30.

## Executables
- `SLPM_860.16` (boot; 307,200 bytes, loads at 0x800D0400 per its header, pc 0x800DF77C). Only 7 Japanese characters. File 0x2C8E0 onward holds `{size, lba, ram}` records, ending with `{0xEA40, 1212, 0x80010010}` (FIX.BIN), `{0x800, 300, 0x80010010}` (PAW.EXE header), then `{0xBC000, 301, ...}` whose third word does not look like an address. **guess**: boot loads 0xBC000 bytes of PAW.EXE's image, not the 0x18E800 its header claims. Its code is not read yet.
- `PAW.EXE` (main; 1,634,304 bytes): header t_addr 0x80010010, t_size 0x18E800, pc 0x8007FC10. **verified** on a story-screen RAM dump (`work/qa/d2`): of the first 0xBC000 bytes, 0xB72D8 match RAM at 0x80010010. Past that, 0x74820 of 0xD2800 match, and that tail is almost all zeros (only 0xAF78 nonzero bytes), so those matches prove little. Anything the patch needs at run time belongs in the first 0xBC000 until the boot code is read.
- `$gp` is 0 in the header; check for `$gp`-relative data before relying on `lui` xrefs alone (not read yet, **guess** that it is unused).

## File records
12-byte `{u32 ram, u32 size, u32 lba}` entries (**verified**: the loader's id table `tools/disc_ids.py` reads them in this order, `docs/re/flow.md`; `tools/disc_tables.py` still prints the columns one word off, as `{size, lba, ram}`, and its "ram" column belongs to the next record). It finds 201 in PAW.EXE (file 0x8B658-0x8C960) and 5 in the boot EXE; listing in
`work/recon/file_tables.tsv`. The scan keeps only records whose LBA starts a known file and whose next word is 0x80xxxxxx, so it misses records like the boot EXE's last one. **verified**: FIX.BIN size 0xEAC0, LBA 1212, sizes and LBAs match the ISO directory.
- Some records use a size rounded up (X_PENTA 0xEA2F vs ISO 0xEA2B). Records exist for P_*, PUP_*, MTIT, X_*, OP*, BAKU*, BATTLE*, S_*.
- Not named by those 201 records, found by reading the code and scanning every small file for `{size, lba}` pairs:
  | Family | How the LBA is made | Where | Label |
  |---|---|---|---|
  | BK_DT 3,349 | `0x3AC7 + 47n`, also +0x1B and +0x24 for its two siblings, written into three PAW records | PAW 0x80033380 | **verified** code read |
  | BTL 2,115 | `0x11940 + 16n` (32 KB each), written into PAW records | PAW 0x8002A5E4, indices from 0x80013FC8 | **verified** code read |
  | ATAMA 353 | `0x2A7B0 + 4n` (8 KB each) for 352 of them; the loader of `ATAMA.BIN` itself was not read | PAW 0x8002A5EC | **verified** code read |
  | NYANTV 125 | `0x1FA4 + 51(n-1)`, or `(n-2)` for n >= 0x1D, so n 28 and 29 share a file (no `TV_028` on disc); n = `G+0x7F7` | PAW 0x80060B0C, record 0x8009C16C | **verified**: code, plus a poke in the `nyantv` scene |
  | BTLEND 17 | Records in the overlay | `BEND_OV` file 0x1A8C | **verified** by scan |
  | ENDING 118 | 165 records in the overlay | `ENDING.BIN` file 0x3AC8 | **verified** by scan |
  | DEMO: COL, SEQ, TXT | 8 x 8 tables in the overlay (`flow.md`) | `MAP_DEMO` | **verified** |
  | DEMO: WMAP, KABE, `*_0n` scenery | WMAP in `SELECT.BIN` file 0xA99C; `*_0n` by `SEQ_*`, whose first words are RAM pointers | `SEQ_*` | **guess** for `*_0n` |
  | Overlays 35 | id table 0x8009C34C, plus map sub-state handlers | `flow.md` | **verified** |
  | SOUND, STR | Not read | | unknown; these are not patched |
  
  Every one of these LBAs is compiled in, so the rebuild rule below covers them all. In phase 3, confirm the `*_0n` route only if one of those files must grow.

## Rebuild rule
**File sizes and LBAs are compiled in.** Keep every file at its LBA, and within its allocated sectors (`layout.xml` records `dummy` gaps). A file that outgrows
its sectors needs its records rewritten or a relocation plan. Keep the file-record size equal to the bytes the game must read.

## Padding
Allocated sectors past a file's real data hold leftover bytes from the mastering PC (a DOS filer's Japanese help: `[eXec] プログラムの実行`, `ドライブ番号`). **verified** by inspection of DEMO files: those strings sit past the LZ
length. They are not game text: leave them, and teach `jp_left.py` to ignore them.

## Free space (candidates only, none tested)
- PAW.EXE zero runs: 0xB33B8 (0x88438 bytes, RAM 0x800C2BC8-0x8014B000) is runtime BSS, **not free**: the text context lives at 0x800C44E0. 0x14EBF1 (0x29BFF), 0x13B7F1 (0xA7FF), 0x145FF1 (0x6FFF),
  0x1787F1 (0x6727) sit where overlays and files load (0x80154000+, 0x80160000, 0x801A0000), so assume **not free** until a RAM watch says otherwise.
- **Best candidate:** the kanji part of the font (file 0x93EC0 + 492*18 up to about 0xA3BE0, ~53 KB, RAM 0x800A36D0+). Once all shipped text is English, those cells are unused (`font.md`). It needs a tour with the
  cells filled with a trap pattern, since any Japanese text left on screen would read them.
- RAM load areas seen: `0x801A0000` (compressed demo graphics), `0x801C0000` (SEQ), `0x801D0000` (story text), `0x801DE000` (LZ window, 1 KB), `0x80154000-0x80160000` (MAP_DEMO at 0x80157000, SEL_HELP at 0x80156800, BKAO_COL at 0x80143850).
