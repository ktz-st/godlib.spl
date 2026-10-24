; DCK-inspired fixed-curve multiscroller. Original DCK kernel builder:
; TEXT $076C-$085C. GodLib adaptation uses MOVEP.L for all four planes.
; No frame cache: generated instruction streams + mirrored column pointers.
        section text
        xdef Dck_Init,Dck_Advance,Dck_Draw,Dck_RuntimeEnd
        xdef Dck_Build,Dck_Font,Dck_Palette,Dck_Paths
        xref gDckCode,gDckColumns,gDckState,gDckScreen,gDckCount
Dck_Init:
        movem.l d0-d7/a0-a6,-(sp)
        lea gDckState,a3
        lea Dck_TextPointers,a4
        lea gDckColumns,a5
        moveq #2,d7
.state:
        move.l (a4)+,d0
        move.l d0,(a3)
        move.l d0,4(a3)
        lea Dck_Font+48*640,a0
        move.l a0,8(a3)
        clr.l 12(a3)
        moveq #79,d6
.blank: move.l a0,(a5)+
        dbf d6,.blank
        lea 16(a3),a3
        dbf d7,.state
        bsr Dck_Build
        ; Prime the window, so the demo opens with text already on screen.
        moveq #39,d7
.prime: bsr Dck_Advance
        dbf d7,.prime
        movem.l (sp)+,d0-d7/a0-a6
        rts
Dck_Build:
        lea gDckCode,a0
        lea Dck_Paths,a3
        moveq #2,d7
.curve: moveq #0,d3
        moveq #39,d6
.col:
        move.w #$205a,(a0)+      ; movea.l (a2)+,a0
        move.w (a3)+,d2
        mulu.w #160,d2
        move.w d3,d1
        lsr.w #1,d1
        lsl.w #3,d1
        add.w d1,d2
        move.w d3,d1
        andi.w #1,d1
        add.w d1,d2
        moveq #31,d5
.row:
        move.w #$2018,(a0)+      ; move.l (a0)+,d0
        move.w #$01c9,(a0)+      ; movep.l d0,d16(a1)
        move.w d2,(a0)+
        addi.w #160,d2
        dbf d5,.row
        addq.w #1,d3
        dbf d6,.col
        move.w #$4e75,(a0)+
        dbf d7,.curve
        rts
Dck_Advance:
        movem.l d0-d7/a0-a6,-(sp)
        lea gDckState,a3
        lea gDckColumns,a4
        moveq #2,d7
.next:
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
        mulu.w #640,d0
        lea Dck_Font,a1
        adda.l d0,a1
        move.l a1,8(a3)
        move.w #5,14(a3)
.slice:
        move.w 12(a3),d0
        lsl.w #2,d0
        lea 0(a4,d0.w),a1
        move.l 8(a3),(a1)
        move.l 8(a3),160(a1)
        addi.l #128,8(a3)
        subq.w #1,14(a3)
        addq.w #1,12(a3)
        cmpi.w #40,12(a3)
        bne.s .nowrap
        clr.w 12(a3)
.nowrap:
        lea 16(a3),a3
        lea 320(a4),a4
        dbf d7,.next
        movem.l (sp)+,d0-d7/a0-a6
        rts
Dck_Draw:
        movem.l d0-d7/a0-a6,-(sp)
        lea gDckState,a3
        lea gDckColumns,a4
        lea gDckCode,a5
        move.w gDckCount,d7
        subq.w #1,d7
.lane:
        move.l gDckScreen,a1
        move.w 12(a3),d0
        lsl.w #2,d0
        lea 0(a4,d0.w),a2
        jsr (a5)
        lea 7762(a5),a5
        lea 16(a3),a3
        lea 320(a4),a4
        dbf d7,.lane
        movem.l (sp)+,d0-d7/a0-a6
        rts
Dck_RuntimeEnd:
        section data
Dck_TextPointers: dc.l Dck_Text0,Dck_Text1,Dck_Text2
        include "assets/text.inc"
Dck_Font:
        incbin "assets/FONT.BIN"
Dck_Palette:
        incbin "assets/PALETTE.BIN"
Dck_Paths:
        incbin "assets/PATHS.BIN"
        even
