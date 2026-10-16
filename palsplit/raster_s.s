; Palette_HBL pattern from Amberstar (NUCLEUS/HBI.ASM): preload, wait, MOVEM.
        section text
        xdef PalSplit_TimerB
        xdef PalSplit_TimerBEnd
        xref gPalSplitGrey
        xref gPalSplitActive
        xref gPalSplitTimerCMask
PalSplit_TimerB:
        movem.l d0-d7/a0-a2,-(sp)
        tst.w gPalSplitActive
        beq.s .stop
; Load all 32 bytes BEFORE waiting for the end of picture row 99.
        lea gPalSplitGrey,a0
        movem.l (a0),d1-d7/a1
        lea $ffff8240.w,a2
; As in Amberstar, restart event counting with a dummy value. Its next change
; marks the next DE falling edge, independent of its previous reload value.
        clr.b $fffffa1b.w
        moveq #8,d0
        move.b d0,$fffffa21.w
        move.b #8,$fffffa1b.w
.wait:
        cmp.b $fffffa21.w,d0
        beq.s .wait
; Sixteen colour words = eight longwords, sent in one MOVEM instruction.
        movem.l d1-d7/a1,(a2)
.stop:
        clr.b $fffffa1b.w
        tst.w gPalSplitTimerCMask
        beq.s .ack
        bset #5,$fffffa15.w
.ack:
        bclr #0,$fffffa0f.w
        movem.l (sp)+,d0-d7/a0-a2
        rte
PalSplit_TimerBEnd:

        section data
        even
        xdef gPalSplitPicture
; Degas low resolution word, 16 ST palette words, 32000 pixel bytes.
gPalSplitPicture:
        incbin "COAST.PI1"
