; DCK bitmap wave adaptation. Interleaved 320x160, stride 160, no frame cache.
; Common one/two-pixel changes use DCK's carry chain. Missing edge bits come
; from the immutable picture; reversals cannot progressively erode the image.
        section text
        xdef Dw_Select,Dw_SelectEnd,Dw_Frame,Dw_FrameEnd
        xdef Dw_Draw,Dw_DrawEnd,Dw_Plane,Dw_PlaneEnd,Dw_Show,Dw_ShowEnd
        xref gDwDest,gDwCursor,gDwOldCursor,gDwOldMask
        xref gDwMask,gDwPhase,gDwPaused
Dw_Select:
        moveq #0,d0
        move.w gDwPhase,d0
        andi.w #255,d0
        lea Dw_Shifts,a0
        adda.w d0,a0
        move.l a0,gDwCursor
        rts
Dw_SelectEnd:
Dw_Frame:
        tst.w gDwPaused
        bne.s .select
        addq.w #1,gDwPhase
        andi.w #255,gDwPhase
.select:
        bsr.s Dw_Select
Dw_FrameEnd:
Dw_OnePlane macro
        move.w (a6),d0
        or.w gDwMask,d0
        btst #\1,d0
        beq.w .skip\@
        lea Dw_Zero,a0
        btst #\1,gDwMask+1
        beq.s .new\@
        move.l gDwCursor,a0
.new\@:
        lea Dw_Zero,a1
        btst #\1,1(a6)
        beq.s .old\@
        move.l gDwOldCursor,a1
        move.l (a1),a1
.old\@:
        move.l gDwDest,a2
        lea Dw_Picture,a3
        lea \1*2(a2),a2
        lea \1*2(a3),a3
        bsr.w Dw_Plane
.skip\@:
        endm
Dw_Draw:
        move.l gDwOldMask,a0
        move.w (a0),d0
        cmp.w gDwMask,d0
        bne.s .changed
        move.l gDwOldCursor,a0
        move.l (a0),a0
        cmpa.l gDwCursor,a0
        bne.s .changed
        rts                        ; identical page: pause needs no row scan
.changed:
        movem.l d2-d7/a2-a6,-(sp)
        move.l gDwOldMask,a6
        Dw_OnePlane 0
        Dw_OnePlane 1
        Dw_OnePlane 2
        Dw_OnePlane 3
        move.w gDwMask,(a6)
        move.l gDwOldCursor,a0
        move.l gDwCursor,(a0)
        movem.l (sp)+,d2-d7/a2-a6
        rts
Dw_DrawEnd:
Dw_Plane:
        move.w #159,d5
.row:
        move.b (a0),d6
        cmp.b (a1),d6
        beq.w .next
        ext.w d6                  ; requested displacement
        move.b (a1),d7
        ext.w d7
        move.w d7,d4              ; old displacement / carry refill position
        neg.w d7
        add.w d6,d7               ; signed per-page difference
        cmpi.w #2,d7
        bgt.w .direct
        cmpi.w #-2,d7
        blt.w .direct
        tst.w d7
        bmi.w .left
.right:
        addq.w #1,d4
        moveq #0,d0
        tst.w d4
        bgt.s .rightedge
        move.w (a3),d0
        move.w d4,d2
        neg.w d2
        lsl.w d2,d0
.rightedge:
        add.w d0,d0               ; X = original pixel entering from the left
N       set 0
        rept 20
        roxr.w N(a2)
N       set N+8
        endr
        subq.w #1,d7
        bne.s .right
        bra.w .next
.left:
        subq.w #1,d4
        moveq #0,d0
        tst.w d4
        bmi.s .leftblank
        move.w 152(a3),d0
        lsr.w d4,d0
        lsr.w #1,d0               ; X = original pixel entering from the right
        bra.s .leftedge
.leftblank:
        add.w d0,d0
.leftedge:
N       set 152
        rept 20
        roxl.w N(a2)
N       set N-8
        endr
        addq.w #1,d7
        bne.s .left
        bra.w .next
; Cold path for mode switches and large phase jumps: compose each word once
; from adjacent ORIGINAL words. Guard words at the two outer edges are zero.
.direct:
        move.l a2,a4
        move.l a3,a5
        move.w d6,d4
        bmi.s .directleft
        moveq #0,d1
        moveq #19,d3
.directright:
        move.w (a5),d0
        move.l d1,d2
        swap d2
        move.w d0,d2
        lsr.l d4,d2
        move.w d2,(a4)
        move.w d0,d1
        lea 8(a5),a5
        lea 8(a4),a4
        dbf d3,.directright
        bra.s .next
.directleft:
        neg.w d4
        moveq #18,d3
.leftword:
        move.w (a5),d0
        swap d0
        move.w 8(a5),d0
        lsl.l d4,d0
        swap d0
        move.w d0,(a4)
        lea 8(a5),a5
        lea 8(a4),a4
        dbf d3,.leftword
        move.w (a5),d0
        lsl.w d4,d0
        move.w d0,(a4)
.next:
        addq.l #2,a0
        addq.l #2,a1
        lea 160(a2),a2
        lea 160(a3),a3
        dbf d5,.row
        rts
Dw_PlaneEnd:
Dw_Show:
        move.l gDwDest,a1
        lea Dw_Picture,a0
        move.w #159,d0
.row:
        rept 40
        move.l (a0)+,(a1)+
        endr
        dbf d0,.row
        rts
Dw_ShowEnd:
        section data
        even
        xdef Dw_Picture,Dw_Palette,Dw_Shifts,Dw_Zero,Dw_Masks
Dw_Masks: dc.w 15,2,5
Dw_Palette: incbin "assets/PALETTE.BIN"
Dw_Picture: incbin "assets/PICTURE.BIN"
Dw_Shifts: incbin "assets/SHIFTS.BIN"
Dw_Zero: dcb.b 320,0
        even
