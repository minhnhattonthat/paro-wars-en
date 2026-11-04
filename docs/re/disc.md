# Disc layout

Single MODE2/2352 data track, 702,250,752 bytes, 6,885 ISO files. Serial SLPM-86016. Unpacks with dumpsxiso 2.30.

## Executables
- `SLPM_860.16` (boot; 307,200 bytes, loads at 0x800D0400 per its header, pc 0x800DF77C): holds 5 file records (0x2C8E8-0x2C918), one of
  which loads `PAW.EXE` (LBA 0x12C, RAM 0x80010010). Only 7 Japanese characters. **verified** (records); what else it does is not read yet.
- `PAW.EXE` (main; 1,634,304 bytes): header t_addr 0x80010010, t_size 0x18E800, pc 0x8007FC10. **verified**: its image matches RAM at 0x80010010 outside the
  areas the game rewrites (`work/qa/d2` RAM dump).
- `$gp` is 0 in the header; check for `$gp`-relative data before relying on `lui` xrefs alone (not read yet, **guess** that it is unused).

## File records
12-byte `{u32 size, u32 lba, u32 ram}` entries. `tools/disc_tables.py` finds 201 in PAW.EXE (file 0x8B658-0x8C960) and 5 in the boot EXE; listing in
`work/recon/file_tables.tsv`. **verified**: FIX.BIN `{0xEAC0, 1212, 0x80160000}`, sizes and LBAs match the ISO directory.
- Some records use a size rounded up (X_PENTA 0xEA2F vs ISO 0xEA2B). Records exist for P_*, PUP_*, MTIT, X_*, OP*, BAKU*, BATTLE*, S_*.
- Not named by these records: BK_DT 3347, BTL 2115, ATAMA 353, DEMO 324, ENDING 118, NYANTV 124, BTLEND 17, overlays and others in DATA 216, SOUND, STR. **guess**: those
  use computed LBAs (base + index), other table shapes, or per-scene lists such as `DEMO/SEQ_*` (their first words are RAM pointers 0x801C0140...). Find the loader in phase 2/3 before changing any file's size.

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
