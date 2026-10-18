; Centred CRT power effect. No runtime division or per-pixel loops.
        section text
        xdef Crt_TvRender,Crt_TvRenderEnd
        xref gCrtScreen,gCrtTvSource,gCrtTvStep,gCrtTvPageHeight,gCrtTvRows
        xref Crt_TvSteps
Crt_TvRender:
        movem.l d2-d7/a2-a6,-(sp)
        move.w gCrtTvStep,d0
        lsl.w #3,d0
        lea Crt_TvSteps,a4
        adda.w d0,a4
        move.w 2(a4),d6         ; new height (0..200)
        move.l gCrtTvPageHeight,a5
        move.w (a5),d7         ; this page's old height
        move.w d6,(a5)
        cmp.w d6,d7
        ble.s .draw
; Clear the two newly uncovered full-width strips, not a whole framebuffer.
        move.w #200,d0
        sub.w d7,d0
        lsr.w #1,d0
        move.w #200,d1
        sub.w d6,d1
        lsr.w #1,d1
        sub.w d0,d1
        bsr .clear
        move.w #200,d0
        add.w d6,d0
        lsr.w #1,d0
        move.w d7,d1
        sub.w d6,d1
        lsr.w #1,d1
        bsr .clear
.draw:
        tst.w d6
        beq .done
        move.l 4(a4),d0
        beq .light
; Image row maps are absolute unsigned byte offsets (<32000).
        move.l d0,a2
        move.w #200,d0
        sub.w d6,d0
        lsr.w #1,d0
        move.l gCrtTvRows,a3
        move.w d0,d1
        add.w d1,d1
        adda.w d1,a3
        mulu.w #160,d0
        move.l gCrtScreen,a1
        adda.l d0,a1
        move.w d6,d7
        subq.w #1,d7
.row:
        move.w (a2)+,d0
        cmp.w (a3),d0
        beq.s .skip
        move.w d0,(a3)+
        move.l gCrtTvSource,a0
        adda.w d0,a0
; 160 bytes: four 40-byte MOVEM bursts, no generic memcpy call per row.
        rept 4
        movem.l (a0)+,d0-d6/a4-a6
        movem.l d0-d6/a4-a6,(a1)
        lea 40(a1),a1
        endr
        dbf d7,.row
        bra.s .done
.skip:
        addq.l #2,a3
        lea 160(a1),a1
        dbf d7,.row
.done:
        movem.l (sp)+,d2-d7/a2-a6
        rts
; A 2-pixel core with a faint 4-pixel halo; the final short line fades away.
; Clear at most four rows, then fill spans with word edge masks.
.light:
        move.l a4,-(sp)
        move.w #200,d0
        sub.w d6,d0
        lsr.w #1,d0
        move.w d6,d1
        bsr .clear
        move.l (sp)+,a4
        move.w #200,d0
        sub.w d6,d0
        lsr.w #1,d0
        mulu.w #160,d0
        move.l gCrtScreen,a1
        adda.l d0,a1
        move.w d6,d7
        subq.w #1,d7
        moveq #1,d5            ; colour index 1: faint outer halo
        cmpi.w #4,d6
        bne.s .core
        move.w (a4),d4
        bsr .span
        lea 160(a1),a1
.core:
        moveq #7,d5            ; colour index 7: two-pixel bright core
        move.w (a4),d4
        bsr .span
        lea 160(a1),a1
        move.w (a4),d4
        bsr .span
        cmpi.w #4,d6
        bne .done
        lea 160(a1),a1
        moveq #1,d5
        move.w (a4),d4
        bsr .span
        bra .done
; d4 centred even span width, d5 colour (1 or 7). Plane3 remains clear.
.span:
        move.w #320,d0
        sub.w d4,d0
        lsr.w #1,d0            ; left pixel
        move.w d0,d1
        andi.w #15,d1
        lsr.w #4,d0
        lsl.w #3,d0
        lea (a1,d0.w),a0
        moveq #-1,d2
        lsr.w d1,d2
        moveq #16,d3
        sub.w d1,d3
        sub.w d3,d4
        bge.s .word
        neg.w d4
        moveq #-1,d0
        lsl.w d4,d0
        and.w d0,d2
        bra.s .last
.word:
        move.w d2,(a0)
        cmpi.w #1,d5
        beq.s .halo_word
        move.w d2,2(a0)
        move.w d2,4(a0)
.halo_word:
        lea 8(a0),a0
        subi.w #16,d4
        bmi.s .tail
        moveq #-1,d2
        bra.s .word
.tail:
        addi.w #16,d4
        beq.s .span_done
        moveq #16,d0
        sub.w d4,d0
        moveq #-1,d2
        lsl.w d0,d2
.last:
        move.w d2,(a0)
        cmpi.w #1,d5
        beq.s .span_done
        move.w d2,2(a0)
        move.w d2,4(a0)
.span_done:
        rts
; Clear d1 rows starting at d0; preserve d6/d7/a4/a5 (height/step).
.clear:
        tst.w d1
        beq.s .clear_done
        move.l d6,-(sp)
        move.l d7,-(sp)
        move.l gCrtTvRows,a3
        move.w d0,d2
        add.w d2,d2
        adda.w d2,a3
        mulu.w #160,d0
        move.l gCrtScreen,a0
        adda.l d0,a0
        move.w d1,d7
        subq.w #1,d7
        moveq #0,d0
        moveq #0,d1
        moveq #0,d2
        moveq #0,d3
        moveq #0,d4
        moveq #0,d6
.clear_row:
        move.w #-1,(a3)+
        rept 5
        movem.l d0-d4/d6,(a0)
        lea 24(a0),a0
        endr
        movem.l d0-d4/d6,(a0)
        lea 24(a0),a0
        movem.l d0-d3,(a0)
        lea 16(a0),a0
        dbf d7,.clear_row
        move.l (sp)+,d7
        move.l (sp)+,d6
.clear_done:
        rts
Crt_TvRenderEnd:
        include 'assets/TVSTEPS.S'
