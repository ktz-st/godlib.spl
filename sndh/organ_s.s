; Static RGB lamps; frame updates touch only palette registers 1, 2 and 4.
        section text
        xdef PsgOrgan_Init,PsgOrgan_Update,PsgOrgan_UpdateEnd
; a0 = Back VRAM, 320x200, 160-byte stride. One-time 1-plane circle stamps.
PsgOrgan_Init:
        movem.l d2-d3/a2,-(sp)
        lea 72*160+24(a0),a2
        moveq #2,d3
.channel:
        move.l a2,a0
        lea Organ_Mask,a1
        moveq #56,d1
.row:
        move.w (a1)+,d2
        or.w d2,(a0)
        move.w (a1)+,d2
        or.w d2,8(a0)
        move.w (a1)+,d2
        or.w d2,16(a0)
        move.w (a1)+,d2
        or.w d2,24(a0)
        lea 160(a0),a0
        dbf d1,.row
        adda.w #42,a2          ; +80px and next plane
        dbf d3,.channel
        movem.l (sp)+,d2-d3/a2
        rts
; a0 = existing VU levels[3], or NULL to black out the lamps (V key).
; 0 = silence, fixed volume 1..15 -> states 2..16, envelope -> state 16.
PsgOrgan_Update:
        move.l a0,d0
        beq.s .off
        lea Organ_Palette(pc),a1
        move.w (a0)+,d0
        add.w d0,d0
        move.w (a1,d0.w),$ffff8242.w
        move.w (a0)+,d0
        add.w d0,d0
        move.w 34(a1,d0.w),$ffff8244.w
        move.w (a0),d0
        add.w d0,d0
        move.w 68(a1,d0.w),$ffff8248.w
        rts
.off:
        clr.w $ffff8242.w
        clr.w $ffff8244.w
        clr.w $ffff8248.w
        rts
PsgOrgan_UpdateEnd:
Organ_Palette:
        incbin 'assets/ORGANPAL.BIN'
        section data
        even
Organ_Mask:
        incbin 'assets/ORGAN.BIN'
