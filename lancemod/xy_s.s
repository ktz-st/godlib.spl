; ICE / Digital World II MODOSC.S, Techwave: oscillo_l/r, xyput, pixels_clear.
; Adapted to vasm/GCC fastcall, ordinary 320x200 screen and GodLib's PCM getters.
; Two delayed stereo XY plots: X=sample[t+64], Y=sample[t], 100 points per side.
; A0 screen, A1 interleaved S8 PCM[328], 4(SP) U16 oldOffsets[200] for this page.
; Old offsets begin at $ffff. Clear all old words before OR-plotting new points:
; repeated points must not XOR-cancel (silence should be one visible dot).
        section text
        xdef XYVis_Draw
XYVis_Draw:
        movem.l d2-d7/a2-a6,-(sp)
        move.l a0,a3
        move.l 48(sp),a2
        move.l a2,a5
        move.w #199,d7
.clear:
        move.w (a2)+,d0
        cmpi.w #32000,d0
        bhs.s .skip
        clr.w (a3,d0.w)
.skip:
        dbf d7,.clear
        move.l a5,a2
        lea XYVis_YOffsets(pc),a4
        moveq #99,d7
.point:
        moveq #0,d0
        move.b 128(a1),d0
        eori.b #$80,d0
        lsr.w #1,d0
        add.w #16,d0
        moveq #0,d1
        move.b (a1)+,d1
        eori.b #$80,d1
        lsr.w #2,d1
        bsr.s .plot
        moveq #0,d0
        move.b 128(a1),d0
        eori.b #$80,d0
        lsr.w #1,d0
        add.w #176,d0
        moveq #0,d1
        move.b (a1)+,d1
        eori.b #$80,d1
        lsr.w #2,d1
        bsr.s .plot
        dbf d7,.point
        movem.l (sp)+,d2-d7/a2-a6
        rts
.plot:
        add.w d1,d1
        move.w (a4,d1.w),d2
        move.w d0,d3
        lsr.w #4,d3
        lsl.w #3,d3
        add.w d3,d2
        move.w d2,(a2)+
        andi.w #15,d0
        move.w #$8000,d3
        lsr.w d0,d3
        or.w d3,(a3,d2.w)
        rts
XYVis_YOffsets:
row set 68
        rept 64
        dc.w row*160
row set row+1
        endr
