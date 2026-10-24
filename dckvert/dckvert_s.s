; DCK-inspired one-pixel vertical text columns for GodLib/68000.
; Four planes, BIG 40x32, row-pointer rings; no screen copy or frame cache.
        section text
        xdef Vert_Init,Vert_Advance,Vert_Draw,Vert_RuntimeEnd
        xdef Vert_Font,Vert_Palette
        xref gVertState,gVertRows,gVertScreen,gVertCount
Vert_Init:
        movem.l d0-d7/a0-a6,-(sp)
        lea gVertState,a3
        lea Vert_TextPointers,a4
        lea gVertRows,a5
        moveq #2,d7
.state:
        move.l (a4)+,d0
        move.l d0,(a3)
        move.l d0,4(a3)
        lea Vert_Font+48*640,a0
        move.l a0,8(a3)
        clr.l 12(a3)
        move.w #287,d6
.blank: move.l a0,(a5)+
        dbf d6,.blank
        lea 16(a3),a3
        dbf d7,.state
        move.w #143,d7
.prime: bsr Vert_Advance
        dbf d7,.prime
        movem.l (sp)+,d0-d7/a0-a6
        rts
Vert_Advance:
        movem.l d0-d7/a0-a6,-(sp)
        lea gVertState,a3
        lea gVertRows,a4
        moveq #2,d7
.next:
        tst.w 14(a3)
        bne.s .row
        move.l 4(a3),a0
        moveq #0,d0
        move.b (a0)+,d0
        cmpi.b #255,d0
        bne.s .glyph
        move.l (a3),a0
        move.b (a0)+,d0
.glyph:
        move.l a0,4(a3)
        mulu.w #640,d0
        lea Vert_Font,a0
        adda.l d0,a0
        move.l a0,8(a3)
        move.w #40,14(a3)
.row:
        lea Vert_Font+48*640,a0
        cmpi.w #8,14(a3)
        bls.s .gap
        move.l 8(a3),a0
        addi.l #20,8(a3)
.gap:
        move.w 12(a3),d0
        lsl.w #2,d0
        lea 0(a4,d0.w),a1
        move.l a0,(a1)
        move.l a0,576(a1)
        subq.w #1,14(a3)
        addq.w #1,12(a3)
        cmpi.w #144,12(a3)
        bne.s .nowrap
        clr.w 12(a3)
.nowrap:
        lea 16(a3),a3
        lea 1152(a4),a4
        dbf d7,.next
        movem.l (sp)+,d0-d7/a0-a6
        rts
Vert_Draw:
        movem.l d0-d7/a0-a6,-(sp)
        lea gVertState,a3
        lea gVertRows,a4
        lea Vert_XOffsets,a5
        move.w gVertCount,d7
        subq.w #1,d7
.lane:
        move.l gVertScreen,a1
        adda.w (a5)+,a1
        move.w 12(a3),d0
        lsl.w #2,d0
        lea 0(a4,d0.w),a2
        move.w #143,d6
.row:
        move.l (a2)+,a0
        movem.l (a0),d0-d4
        movem.l d0-d3,(a1)
        movep.l d4,16(a1)
        lea 160(a1),a1
        dbf d6,.row
        lea 16(a3),a3
        lea 1152(a4),a4
        dbf d7,.lane
        movem.l (sp)+,d0-d7/a0-a6
        rts
Vert_RuntimeEnd:
        section data
Vert_XOffsets: dc.w 28*160+24,28*160+72,28*160+120
Vert_TextPointers: dc.l Vert_Text0,Vert_Text1,Vert_Text2
        include "assets/text.inc"
Vert_Font:
        incbin "assets/FONT.BIN"
Vert_Palette:
        incbin "assets/PALETTE.BIN"
        even
