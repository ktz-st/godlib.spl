; Single-colour raster list inspired by Amberstar's Single_HBL/Palette_HBL.
; Four-line bands, synchronized writes; no self-modifying instruction operands.
        section text
        xdef Raster_TimerB
        xdef Raster_TimerBEnd
        xref gRasterActive
        xref gRasterNext
        xref gRasterRemaining
        xref gRasterTimerCMask
Raster_TimerB:
        movem.l d0-d1/a0,-(sp)
        tst.w gRasterActive
        beq.s .finish
        move.l gRasterNext,a0
        move.w 2(a0),d1
        addq.l #4,a0
        move.l a0,gRasterNext
; Enter one event early, then synchronize to the actual boundary with the
; dummy-counter pattern used by Amberstar's palette handler.
        clr.b $fffffa1b.w
        moveq #8,d0
        move.b d0,$fffffa21.w
        move.b #8,$fffffa1b.w
.wait:
        cmp.b $fffffa21.w,d0
        beq.s .wait
        move.w d1,$ffff8240.w
        clr.b $fffffa1b.w
        subq.w #1,gRasterRemaining
        beq.s .finish
; The next record's count is relative to this completed boundary.
        move.b (a0),$fffffa21.w
        move.b #8,$fffffa1b.w
        bra.s .ack
.finish:
        clr.b $fffffa1b.w
        tst.w gRasterTimerCMask
        beq.s .ack
        bset #5,$fffffa15.w
.ack:
        bclr #0,$fffffa0f.w
        movem.l (sp)+,d0-d1/a0
        rte
Raster_TimerBEnd:
