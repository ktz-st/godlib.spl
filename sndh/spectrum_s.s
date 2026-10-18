; POV93 / Mac Sys Data: 80 note bands, height 12, mirrored about a horizontal
; axis. Rewritten as per-page delta drawing for a 320x200 GodLib canvas.
        section text
        xdef PsgSpectrum_Draw,PsgSpectrum_DrawEnd
; a0=screen, a1=80 byte heights, 4(sp)=80 previous byte heights.
PsgSpectrum_Draw:
        movem.l d2-d7/a2-a6,-(sp)
        move.l 48(sp),a4
        lea 99*160(a0),a2
        lea PsgSpectrum_Rows(pc),a6
        move.w #$e000,d4
        moveq #79,d7
.bar:
        moveq #0,d0
        moveq #0,d1
        move.b (a1)+,d0
        move.b (a4),d1
        move.b d0,(a4)+
        cmp.w d1,d0
        beq.s .next
        move.l a2,a0
        lea 160(a2),a3
        bhi.s .grow
; shrink: erase rows [new,old).
        sub.w d0,d1
        add.w d0,d0
        move.w (a6,d0.w),d0
        suba.w d0,a0
        adda.w d0,a3
        move.w d4,d5
        not.w d5
        subq.w #1,d1
.erase:
        and.w d5,(a0)
        and.w d5,(a3)
        lea -160(a0),a0
        lea 160(a3),a3
        dbf d1,.erase
        bra.s .next
.grow:
        sub.w d1,d0
        add.w d1,d1
        move.w (a6,d1.w),d1
        suba.w d1,a0
        adda.w d1,a3
        subq.w #1,d0
.draw:
        or.w d4,(a0)
        or.w d4,(a3)
        lea -160(a0),a0
        lea 160(a3),a3
        dbf d0,.draw
.next:
        ror.w #4,d4
        bpl.s .sameword
        addq.l #8,a2
.sameword:
        dbf d7,.bar
        movem.l (sp)+,d2-d7/a2-a6
        rts
PsgSpectrum_DrawEnd:
PsgSpectrum_Rows:
N       set 0
        rept 13
        dc.w N*160
N       set N+1
        endr
