; English text for PAW.EXE: replaces the per-character loop of the text-window draw routine 0x80067640 (docs/re/font.md).
; A halfword below 0x8000 holds two 7-bit letters, each drawn as its own POLY_FT4 from the fixed glyph slots, at a proportional
; advance. A halfword from 0x8000 up is a fullwidth Shift-JIS code, drawn as before at 12 px. $s6 now counts pixels, not columns.
; Run from build/tmp: armips vwf.asm, with paw_in.exe and widths.bin there. Registers in the loop:
;   s3 window, s4 text context, s5 text pointer, s6 pen x in px, fp line, s7 main prim, 0x40(sp) shadow prim
; Stack frame of 0x80067640 is 0xA8; 0x64 and 0x68 are unused by it.
.psx
.open "paw_in.exe","paw_out.exe",0x80010010-0x800

SLOT_FIRST equ 62               ; glyph slot of letter 0x20: the first hiragana slot, see tools/en_text.py
LOOP_END   equ 0x80067CEC       ; the routine's own code after the loop
ADVANCES   equ (LOOP_END - 0x60)
LOOKUP     equ 0x800671E0       ; (ctx, code, &cell) -> slot byte or -1
LOADGLYPH  equ 0x8006725C       ; (ctx, slot, &code, cell)
FX_CORNERS equ 0x800763A0       ; (table byte, x, y, w, h, &xy0, &xy1, &xy2, &xy3), for transformed windows
FX_TABLE   equ 0x801425B7

; Two prims per code: the two places the routine sizes its share of the frame pool from the code count.
.org 0x800676F8
    sll   v0,v0,4
.org 0x80067734
    sll   v0,v0,4

.org 0x800677A0
next:
    lhu   s2,0(s5)
    nop
    addiu v1,s2,0x7DB1          ; fullwidth digits draw as the proportional font's digits, so numbers the code writes take half the room
    andi  v1,v1,0xFFFF
    sltiu v0,v1,10
    bnez  v0,digit
    addiu a0,v1,0x30
    andi  v0,s2,0x8000
    beqz  v0,pair
    lui   t0,0x800C
    lw    t0,0x2728(t0)         ; non-zero: draw ＾ and ＠ as glyphs instead of acting on them
    ori   v0,zero,0x814F
    bne   s2,v0,@@not_hat
    ori   v0,zero,0x8197
    beqz  t0,tail               ; ＾: nothing
    nop
@@not_hat:
    bne   s2,v0,@@not_at
    ori   v0,zero,0x8140
    beqz  t0,newline            ; ＠: line break
    nop
@@not_at:
    beq   s2,v0,blank           ; fullwidth space: a digit's advance, so zero-padded numbers stay right-aligned
    move  a0,s4
    move  a1,s2
    jal   LOOKUP
    addiu a2,sp,0x30
    addiu v1,s2,0x7DB1          ; 0x824F-0x839E have fixed slots
    andi  v1,v1,0xFFFF
    sltiu v1,v1,0x150
    bnez  v1,@@mark
    move  s0,v0
    addiu s0,s0,0xE7            ; the rest share the dynamic slots 0xE7-0x1E2
    sll   v0,s0,1
    addu  v0,v0,s4
    lhu   v0,0x111C(v0)
    nop
    beq   v0,s2,@@mark
    lhu   a0,0x14E2(s4)
    li    a2,1
@@find:                         ; next free dynamic slot
    addu  v0,a0,s4
    lbu   v0,0x3D4(v0)
    nop
    bne   v0,a2,@@load
    addiu a0,a0,1
    sltiu v0,a0,0x1E3
    bnez  v0,@@store
    nop
    li    a0,0xE7
@@store:
    b     @@find
    sh    a0,0x14E2(s4)
@@load:
    move  a0,s4
    lhu   a1,0x14E2(s4)
    lh    a3,0x30(sp)
    jal   LOADGLYPH
    move  a2,s5
    lhu   a0,0x14E2(s4)
    lhu   v1,0x30(sp)
    move  s0,a0
    addiu v1,v1,1
    andi  v1,v1,0xFFFF
    sll   v0,v1,3
    addu  v0,v0,v1
    sll   v0,v0,1
    lw    v1,0x14EC(s4)
    addiu a0,a0,0x19            ; the cell's last byte finds this slot next time
    addu  v0,v0,v1
    sb    a0,-1(v0)
@@mark:
    addu  v1,s0,s4
    li    v0,1
    sb    v0,0x3D4(v1)
    move  v1,s0
    li    a3,0xB
    jal   emit
    move  a2,zero
    b     tail                  ; byte 8 of the window, the wrap column, is ignored: English breaks with {br} (tools/limits.py), and a dialog's 7 columns are narrower than its box
    addiu s6,s6,12
digit:
    jal   letter
    nop
    b     tail
    nop
blank:
    b     tail
    addiu s6,s6,6
newline:
    move  s6,zero
    addiu fp,fp,1
tail:
    lhu   t3,0x38(sp)
    li    v1,-1
    addiu v0,t3,-1
    sh    v0,0x38(sp)
    sll   v0,v0,0x10
    sra   v0,v0,0x10
    bne   v0,v1,next
    addiu s5,s5,2
    j     LOOP_END
    nop

pair:
    srl   a0,s2,8
    li    v0,0x1E
    bne   a0,v0,@@letters
    andi  v0,s2,0xFF
    sll   s6,v0,1               ; tab: halfword 0x1E, n sets the pen to 2(n-5) px from the window's x. Biased because a swapped n
    b     tail                  ; comes first in its halfword, and the next prepare's scan ends a string at a byte below 5
    addiu s6,s6,-10
@@letters:
    jal   letter
    nop
    jal   letter
    andi  a0,s2,0xFF
    b     tail
    nop

; a0 = letter byte. 0x1F pads to a halfword and draws nothing, 0x0A is a line break.
letter:
    sw    ra,0x68(sp)
    li    v0,0x1F
    beq   a0,v0,@@done
    li    v0,0x0A
    bne   a0,v0,@@glyph
    addiu a0,a0,-0x20
    move  s6,zero
    b     @@done
    addiu fp,fp,1
@@glyph:
    sltiu v0,a0,0x60
    beqz  v0,@@done             ; not a letter: draw nothing
    la    v0,ADVANCES
    addu  v0,v0,a0
    lbu   a3,0(v0)
    beqz  a0,@@advance          ; space
    nop
    addiu v1,a0,SLOT_FIRST
    sw    a3,0x6C(sp)
    li    a2,-1                 ; column 0 of the cell is the outline
    jal   emit
    addiu a3,a3,1               ; the quad: width + 2 outline columns; the table holds width + 1
    lw    a3,0x6C(sp)
    nop
@@advance:
    addu  s6,s6,a3
@@done:
    lw    ra,0x68(sp)
    nop
    jr    ra
    nop

; v1 = slot (negative: the blank cell), a3 = quad width, a2 = x offset from the pen. Writes the prim and its shadow.
emit:
    sw    ra,0x64(sp)
    bltz  v1,@@blank
    li    t0,0xF4
    li    t0,21
    divu  v1,t0
    mfhi  t0
    mflo  t1
    sll   v0,t0,1
    addu  t0,t0,v0
    sll   t0,t0,2               ; u = column * 12
    sll   v0,t1,1
    addu  v0,v0,t1
    sll   v0,v0,2
    b     @@uv
    subu  t1,v0,t1              ; v = row * 11
@@blank:
    li    t1,0xF4
@@uv:
    addu  t2,t0,a3
    addiu t3,t1,0xB
    sb    t0,0xC(s7)
    sb    t1,0xD(s7)
    sb    t2,0x14(s7)
    sb    t1,0x15(s7)
    sb    t0,0x1C(s7)
    sb    t3,0x1D(s7)
    sb    t2,0x24(s7)
    sb    t3,0x25(s7)
    li    v0,0x80
    sb    v0,4(s7)
    sb    v0,5(s7)
    sb    v0,6(s7)
    li    v0,0x2E
    sb    v0,7(s7)
    li    v0,0x2A
    sh    v0,0x16(s7)
    lhu   v0,0xA(s3)
    nop
    sh    v0,0xE(s7)
    lbu   v0,0x19(s3)           ; y = window y + line * (12 + gap)
    andi  v1,fp,0xFF
    addiu v0,v0,0xC
    mult  v1,v0
    lhu   t1,6(s3)
    mflo  v0
    addu  t1,t1,v0
    lhu   t0,4(s3)
    lw    t3,0x60(sp)
    addu  t0,t0,s6
    bnez  t3,@@transformed
    addu  t0,t0,a2
    addu  t2,t0,a3
    addiu t3,t1,0xB
    sh    t0,8(s7)
    sh    t0,0x18(s7)
    sh    t2,0x10(s7)
    sh    t2,0x20(s7)
    sh    t1,0xA(s7)
    sh    t1,0x12(s7)
    sh    t3,0x1A(s7)
    b     @@link
    sh    t3,0x22(s7)
@@transformed:
    sll   a1,t0,0x10
    sra   a1,a1,0x10
    sll   a2,t1,0x10
    sra   a2,a2,0x10
    li    v0,0xB
    sw    v0,0x10(sp)
    addiu v0,s7,8
    sw    v0,0x14(sp)
    addiu v0,s7,0x10
    sw    v0,0x18(sp)
    addiu v0,s7,0x18
    sw    v0,0x1C(sp)
    addiu v0,s7,0x20
    sw    v0,0x20(sp)
    lui   at,hi(FX_TABLE)
    addu  at,at,t3
    jal   FX_CORNERS
    lbu   a0,lo(FX_TABLE)(at)
@@link:
    lw    v0,0x28(sp)
    lui   t2,0x900
    or    v0,v0,t2
    sw    v0,0(s7)
    lui   t3,0xFF
    ori   t3,t3,0xFFFF
    and   v0,s7,t3
    sw    v0,0x28(sp)
    lbu   v0,0x18(s3)
    nop
    andi  v0,v0,1
    beqz  v0,@@next_prim
    nop
    lw    t1,0x40(sp)           ; shadow: the same quad at the window's offset, another clut and blend
    lb    a0,2(s3)
    lb    a1,3(s3)
    move  t4,t1
    move  t5,s7
    li    t6,3
@@corner:
    lhu   v0,8(t5)
    lhu   v1,0xA(t5)
    addu  v0,v0,a0
    addu  v1,v1,a1
    sh    v0,8(t4)
    sh    v1,0xA(t4)
    lhu   v0,0xC(t5)
    addiu t5,t5,8
    sh    v0,0xC(t4)
    addiu t4,t4,8
    bnez  t6,@@corner
    addiu t6,t6,-1
    li    v0,0x80
    sb    v0,4(t1)
    sb    v0,5(t1)
    sb    v0,6(t1)
    li    v0,0x2E
    sb    v0,7(t1)
    li    v0,0xA
    sh    v0,0x16(t1)
    lhu   v0,0xC(s3)
    nop
    sh    v0,0xE(t1)
    lw    v0,0x2C(sp)
    nop
    or    v0,v0,t2
    sw    v0,0(t1)
    and   v0,t1,t3
    sw    v0,0x2C(sp)
    addiu t1,t1,0x28
    sw    t1,0x40(sp)
@@next_prim:
    addiu s7,s7,0x28
    lw    ra,0x64(sp)
    nop
    jr    ra
    nop

.if org() > ADVANCES
    .error "the loop grew over the width table"
.endif
.org ADVANCES                   ; fixed, tools/debug/boxes.lua reads it
    .incbin "widths.bin"        ; 96 bytes: advance per letter from 0x20, which is glyph width + 1
.if org() > LOOP_END
    .error "the width table must end at the routine's tail"
.endif

; String prepare, 0x80068838 (window a0, text a1), rewritten tighter to add far strings: a slot holding 0x1C, pad, then a 32-bit
; little-endian address stands for the string at that address, so a fixed table field can hold any length (docs/re/font.md).
FAR_MARK equ 0x1C
PREP_END equ 0x800688CC
.org 0x80068838
    lbu   v0,0(a1)
    li    v1,FAR_MARK
    bne   v0,v1,@@near
    move  a2,a1
    lhu   a2,2(a1)
    lhu   v1,4(a1)
    nop
    sll   v1,v1,0x10
    or    a2,a2,v1
@@near:
    sw    a2,0x14(a0)
    move  a1,a2
    move  a3,zero
@@scan:                         ; 2 bytes at a time to a byte below 5; a3 counts codes
    lbu   v0,0(a1)
    nop
    sltiu v0,v0,5
    bnez  v0,@@end
    nop
    addiu a1,a1,2
    b     @@scan
    addiu a3,a3,1
@@end:
    lbu   v1,0(a1)
    sh    a3,0xE(a0)
    bnez  v1,@@ret              ; ended by 1: prepared already
    li    v0,1
    sb    v0,0(a1)
@@swap:                         ; every pair swapped in place, once, so RAM holds little-endian halfwords
    beqz  a3,@@ret
    lbu   v0,0(a2)
    lbu   v1,1(a2)
    sb    v0,1(a2)
    sb    v1,0(a2)
    addiu a2,a2,2
    b     @@swap
    addiu a3,a3,-1
@@ret:
    jr    ra
    nop
.if org() > PREP_END
    .error "prepare grew"
.endif
.close
