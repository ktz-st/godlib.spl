; Four 128-pixel oscilloscope traces: CH1/CH4 left, CH2/CH3 right.
; XOR only the previous/new 2-pixel marks in plane zero; no full-screen copy.
        section text
        xdef ScopeVis_Init,ScopeVis_Draw,ScopeVis_YOffsets
; A0 screen. Initial zero samples represent the four horizontal centre lines.
ScopeVis_Init:
        movem.l d2/a1-a2,-(sp)
        lea ScopeVis_Positions(pc),a2
        moveq #3,d1
.channel:
        move.l a0,a1
        adda.w (a2)+,a1
        moveq #7,d0
.line:
        move.w #$ffff,(a1)
        addq.l #8,a1
        dbf d0,.line
        dbf d1,.channel
        movem.l (sp)+,d2/a1-a2
        rts
; A0 screen, A1 signed samples[256], 4(SP) previous samples[256] for this page.
ScopeVis_Draw:
        movem.l d2-d7/a2-a6,-(sp)
        move.l 48(sp),a2
        move.l a0,a3
        lea ScopeVis_Positions(pc),a5
        lea ScopeVis_YOffsets(pc),a4
        moveq #3,d7
.channel:
        move.l a3,a0
        adda.w (a5)+,a0
        move.w #$c000,d4
        moveq #63,d6
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
        ror.w #2,d4
        bcc.s .sameWord
        addq.l #8,a0
.sameWord:
        dbf d6,.point
        dbf d7,.channel
        movem.l (sp)+,d2-d7/a2-a6
        rts
ScopeVis_Positions:
        dc.w 64*160+8,64*160+88,148*160+88,148*160+8
ScopeVis_YOffsets:
value set 0
        rept 256
        iflt value-128
        dc.w -(value/4)*160
        else
        ; Arithmetic shift: negative samples round toward minus infinity.
        dc.w ((256-value+3)/4)*160
        endc
value set value+1
        endr
