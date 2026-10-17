; Separate stereo traces or one mono average, 128 points.
; Real interleaved native PCM from *_GetStereoOscilloscope, first 128 frames.
; Plane 2 = left (green), plane 3 = right (cyan); mono = plane 0 (white).
        section text
        xdef StereoVis_InitSplit,StereoVis_InitMono
        xdef StereoVis_DrawSplit,StereoVis_DrawMono
        xref ScopeVis_YOffsets
StereoVis_InitMono:
        lea 100*160+16(a0),a0
        moveq #15,d0
.line:
        move.w #$ffff,(a0)
        addq.l #8,a0
        dbf d0,.line
        rts
StereoVis_InitSplit:
        movem.l a2-a3,-(sp)
        lea 64*160+16+4(a0),a2
        lea 148*160+16+6(a0),a3
        moveq #15,d1
.line:
        move.w #$ffff,(a2)
        move.w #$ffff,(a3)
        addq.l #8,a2
        addq.l #8,a3
        dbf d1,.line
        movem.l (sp)+,a2-a3
        rts
; A0 screen, A1 PCM[328], 4(SP) previous samples for this logical page.
StereoVis_DrawSplit:
        movem.l d2-d7/a2-a6,-(sp)
        move.l 48(sp),a2
        lea 148*160+16+6(a0),a6
        lea 64*160+16+4(a0),a0
        lea ScopeVis_YOffsets,a4
        move.w #$c000,d4
        moveq #127,d7
.point:
        moveq #0,d0
        move.b (a2),d0
        add.w d0,d0
        move.w (a4,d0.w),d1
        eor.w d4,(a0,d1.w)
        moveq #0,d0
        move.b (a1)+,d0
        move.b d0,(a2)+
        add.w d0,d0
        move.w (a4,d0.w),d1
        eor.w d4,(a0,d1.w)
        moveq #0,d0
        move.b (a2),d0
        add.w d0,d0
        move.w (a4,d0.w),d1
        eor.w d4,(a6,d1.w)
        moveq #0,d0
        move.b (a1)+,d0
        move.b d0,(a2)+
        add.w d0,d0
        move.w (a4,d0.w),d1
        eor.w d4,(a6,d1.w)
        ror.w #2,d4
        bcc.s .sameWord
        addq.l #8,a0
        addq.l #8,a6
.sameWord:
        dbf d7,.point
        movem.l (sp)+,d2-d7/a2-a6
        rts
StereoVis_DrawMono:
        movem.l d2-d7/a2-a6,-(sp)
        move.l 48(sp),a2
        lea 100*160+16(a0),a0
        lea ScopeVis_YOffsets,a4
        move.w #$c000,d4
        moveq #127,d7
.point:
        moveq #0,d0
        move.b (a2),d0
        add.w d0,d0
        move.w (a4,d0.w),d1
        eor.w d4,(a0,d1.w)
        move.b (a1)+,d0
        ext.w d0
        move.b (a1)+,d1
        ext.w d1
        add.w d1,d0
        asr.w #1,d0
        move.b d0,(a2)+
        and.w #$ff,d0
        add.w d0,d0
        move.w (a4,d0.w),d1
        eor.w d4,(a0,d1.w)
        ror.w #2,d4
        bcc.s .sameWord
        addq.l #8,a0
.sameWord:
        dbf d7,.point
        movem.l (sp)+,d2-d7/a2-a6
        rts
        section data
        xdef gStereoVisPalette
gStereoVisPalette:
        dc.w $000,$777,$555,$333,$070,$050,$030,$733
        dc.w $057,$500,$000,$000,$777,$000,$000,$777
