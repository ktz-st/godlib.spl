; DCK-inspired flat colour scrollers, 68000 / GodLib.
; Two 8px slices per ESCALI glyph. No generated code, bit shifts or frame cache.
        include "assets/config.inc"
        section text
        xdef HS_Init,HS_Advance,HS_Draw,HS_RuntimeEnd,HS_Font,HS_Palette
        xref gHSState,gHSColumns,gHSScreen,gHSCount
HS_Init:
        movem.l d0-d7/a0-a6,-(sp)
        lea gHSState,a3
        lea gHSColumns,a4
        lea HS_TextPointers,a5
        lea HS_Directions,a6
        moveq #HS_LANES-1,d7
.state:
        move.l (a5)+,d0
        move.l d0,(a3)
        move.l d0,4(a3)
        lea HS_Font+HS_Blank,a0
        move.l a0,8(a3)
        clr.l 12(a3)            ; head, remaining glyph slices
        move.w #1,16(a3)        ; tick
        move.w #1,18(a3)        ; prime every update
        move.w (a6)+,20(a3)
        moveq #79,d6
.blank: move.l a0,(a4)+
        dbf d6,.blank
        lea HS_StateSize(a3),a3
        dbf d7,.state
        moveq #39,d7
.prime: bsr HS_Advance
        dbf d7,.prime
        lea gHSState,a3
        lea HS_Periods,a0
        moveq #HS_LANES-1,d7
.period:
        move.w (a0)+,18(a3)
        move.w 18(a3),16(a3)
        lea HS_StateSize(a3),a3
        dbf d7,.period
        movem.l (sp)+,d0-d7/a0-a6
        rts
HS_Advance:
        movem.l d0-d7/a0-a6,-(sp)
        lea gHSState,a3
        lea gHSColumns,a4
        moveq #HS_LANES-1,d7
.next:
        subq.w #1,16(a3)
        bne.w .skip
        move.w 18(a3),16(a3)
        tst.w 14(a3)
        bne.s .slice
        move.l 4(a3),a0
        moveq #0,d0
        move.b (a0)+,d0
        cmpi.b #255,d0
        bne.s .glyph
        move.l (a3),a0
        move.b (a0)+,d0
.glyph:
        move.l a0,4(a3)
        lsl.l #7,d0
        lea HS_Font,a0
        adda.l d0,a0
        tst.w 20(a3)
        bpl.s .leftstart
        lea 64(a0),a0
.leftstart:
        move.l a0,8(a3)
        move.w #2,14(a3)
.slice:
        move.w 12(a3),d0
        tst.w 20(a3)
        bpl.s .left
        subq.w #1,d0
        bpl.s .rightok
        moveq #39,d0
.rightok:
        move.w d0,12(a3)
.left:
        lsl.w #2,d0
        lea 0(a4,d0.w),a1
        move.l 8(a3),(a1)
        move.l 8(a3),160(a1)
        tst.w 20(a3)
        bmi.s .right
        addi.l #64,8(a3)
        addq.w #1,12(a3)
        cmpi.w #40,12(a3)
        bne.s .done
        clr.w 12(a3)
        bra.s .done
.right:
        subi.l #64,8(a3)
.done:
        subq.w #1,14(a3)
.skip:
        lea HS_StateSize(a3),a3
        lea 320(a4),a4
        dbf d7,.next
        movem.l (sp)+,d0-d7/a0-a6
        rts
HS_Draw:
        movem.l d0-d7/a0-a6,-(sp)
        lea gHSState,a5
        lea gHSColumns,a4
        lea HS_YOffsets,a6
        move.w gHSCount,d7
        subq.w #1,d7
.lane:
        move.l gHSScreen,a1
        adda.w (a6)+,a1
        move.w 12(a5),d0
        lsl.w #2,d0
        lea 0(a4,d0.w),a2
        moveq #19,d6
.pair:
        move.l (a2)+,a0
        move.l (a2)+,a3
Y       set 0
        rept 16
        move.l (a0)+,d0
        move.l (a3)+,d1
        movep.l d0,Y(a1)
        movep.l d1,Y+1(a1)
Y       set Y+160
        endr
        addq.l #8,a1
        dbf d6,.pair
        lea HS_StateSize(a5),a5
        lea 320(a4),a4
        dbf d7,.lane
        movem.l (sp)+,d0-d7/a0-a6
        rts
HS_RuntimeEnd:
        section data
        include "assets/tables.inc"
        include "assets/text.inc"
HS_Font:
        incbin "assets/FONT.BIN"
HS_Palette:
        incbin "assets/PALETTE.BIN"
        even
