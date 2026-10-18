; Differential plane-3 spans, sparse white-edge undo, specialized white lines.
        section text
        MACRO mIrisXorSpan
        cmp.w d0,d1
        beq.s .sameWord\@
        bge.s .spanOrdered\@
        exg d0,d1
.spanOrdered\@:
        move.l a6,a0
        adda.w d0,a0
        move.w d1,d2
        sub.w d0,d2
        swap d0
        eor.w d0,(a0)
        adda.w d2,a0            ; rightmost word group
        cmp.w #8,d2
        beq .right\@
        lsr.w #1,d2             ; 4 bytes of code per skipped word
        neg.w d2
        addq.w #4,d2
        jmp .right\@(pc,d2.w)
        not.w -152(a0)
        not.w -144(a0)
        not.w -136(a0)
        not.w -128(a0)
        not.w -120(a0)
        not.w -112(a0)
        not.w -104(a0)
        not.w -96(a0)
        not.w -88(a0)
        not.w -80(a0)
        not.w -72(a0)
        not.w -64(a0)
        not.w -56(a0)
        not.w -48(a0)
        not.w -40(a0)
        not.w -32(a0)
        not.w -24(a0)
        not.w -16(a0)
        not.w -8(a0)
.right\@:
        swap d1
        not.w d1
        beq.s .xorReturn\@
        eor.w d1,(a0)
        bra.s .xorReturn\@
.sameWord\@:
        eor.l d1,d0
        swap d0
        move.l a6,a0
        adda.w d1,a0
        eor.w d0,(a0)
.xorReturn\@:
        ENDM
        xdef Iris_Delta,Iris_DeltaEnd,Iris_Restore,Iris_RestoreEnd
        xdef Iris_WhiteLine,Iris_WhiteLineEnd
Iris_Delta:
; a0 screen, a1 per-page raw inclusive spans. Skip unchanged rows first.
        movem.l d2-d7/a2-a6,-(sp)
        lea 6(a0),a6
        lea Iris_Edges,a2
        lea gIrisSpans,a4
        move.w #199,d7
.row:
        move.l (a4)+,d0
        move.l (a1),d1
        cmp.l d0,d1
        beq .unchanged
        move.l d0,(a1)+
        move.l d0,a3
        move.l d1,a5
        tst.w d0
        bmi .oldOnly
        tst.w d1
        bmi .newOnly
        swap d0
        swap d1
        cmp.w d0,d1
        beq .right
        add.w d0,d0
        add.w d0,d0
        add.w d1,d1
        add.w d1,d1
        move.l (a2,d0.w),d0
        move.l (a2,d1.w),d1
        mIrisXorSpan
.right:
        move.l a3,d0
        move.l a5,d1
        cmp.w d0,d1
        beq .next
        addq.w #1,d0
        addq.w #1,d1
        add.w d0,d0
        add.w d0,d0
        add.w d1,d1
        add.w d1,d1
        move.l (a2,d0.w),d0
        move.l (a2,d1.w),d1
        mIrisXorSpan
        bra .next
.oldOnly:
        move.l a5,d0
        bra.s .oneSpan
.newOnly:
        move.l a3,d0
.oneSpan:
        move.l d0,d1
        swap d0
        addq.w #1,d1
        add.w d0,d0
        add.w d0,d0
        add.w d1,d1
        add.w d1,d1
        move.l (a2,d0.w),d0
        move.l (a2,d1.w),d1
        mIrisXorSpan
        bra.s .next
.unchanged:
        addq.l #4,a1
.next:
        lea 160(a6),a6
        dbra d7,.row
        movem.l (sp)+,d2-d7/a2-a6
        rts
Iris_DeltaEnd:
Iris_Restore:
; a0 display page, a1 clean background. Undo records in reverse order:
; a repeated word at a hexagon vertex is therefore restored correctly.
        movem.l d2/a2-a5,-(sp)
        move.l a0,a2
        move.l a1,a3
        suba.l a0,a3
        move.l gIrisLogEnd,a4
        move.l gIrisLogBase,a5
        move.l a4,d1
        sub.l a5,d1
        beq.s .done
        divu.w #6,d1
        subq.w #1,d1
.loop:
        move.l -(a4),a0
        move.w -(a4),d2
        move.l a0,a1
        adda.l a3,a1
        move.l (a1),(a0)
        move.w 4(a1),4(a0)
        move.w d2,6(a0)
        dbra d1,.loop
.done:
        move.l a5,gIrisLogEnd
        movem.l (sp)+,d2/a2-a5
        rts
Iris_RestoreEnd:
        MACRO mWhiteFlush
        tst.w d6
        beq.s .empty\@
        move.w 6(a0),(a3)+
        move.l a0,(a3)+
        or.l d6,(a0)
        or.l d6,4(a0)
        moveq #0,d6
.empty\@:
        ENDM
Iris_WhiteLine:
; a0 raw screen, a1 clipped sGraphicBox, global per-page sparse undo log.
        movem.l d2-d7/a2-a6,-(sp)
        move.l a0,a2
        move.l gIrisLogEnd,a3
        move.w (a1),d0         ; x0
        move.w 4(a1),d1        ; y0
        move.w d1,d2
        mulu.w #160,d2
        adda.l d2,a0
        move.w d0,d2
        and.w #$fff0,d2
        lsr.w #1,d2
        adda.w d2,a0
        and.w #15,d0
        move.w #$8000,d5
        lsr.w d0,d5
        move.w d5,d0
        swap d5
        move.w d0,d5
        move.w 2(a1),d1
        sub.w (a1),d1         ; dx
        move.w #8,a4
        bge.s .dx
        neg.w d1
        move.w #-8,a4
.dx:
        move.w #160,d7
        move.w 6(a1),d2
        sub.w 4(a1),d2
        bge.s .dy
        neg.w d2
        move.w #-160,d7
.dy:
        move.w d1,d3
        cmp.w d2,d3
        bge.s .count
        move.w d2,d3
.count:
        neg.w d2              ; dy = -abs(y1-y0)
        move.w d1,d4
        add.w d2,d4           ; generic Bresenham error
        moveq #0,d6
        move.w d2,d0
        neg.w d0
        cmp.w d0,d1
        blt .yMajor
        cmpa.w #0,a4
        bmi .xLeft
        bra .xRight
.yMajor:
        cmpa.w #0,a4
        bmi .yLeft
        bra .yRight
.xRight:
        or.l d5,d6
        dbra d3,.stepxRight
        bra .last
.stepxRight:
        move.w d4,d0
        add.w d0,d0
        cmp.w d1,d0
        bgt.s .noYxRight
        add.w d1,d4
        mWhiteFlush
        adda.w d7,a0
.noYxRight:
        add.w d2,d4
        ror.l #1,d5
        bcc .xRight
        mWhiteFlush
        addq.l #8,a0
        bra .xRight
.xLeft:
        or.l d5,d6
        dbra d3,.stepxLeft
        bra .last
.stepxLeft:
        move.w d4,d0
        add.w d0,d0
        cmp.w d1,d0
        bgt.s .noYxLeft
        add.w d1,d4
        mWhiteFlush
        adda.w d7,a0
.noYxLeft:
        add.w d2,d4
        rol.l #1,d5
        bcc .xLeft
        mWhiteFlush
        subq.l #8,a0
        bra .xLeft
.yRight:
        move.l d5,d6
        mWhiteFlush
        dbra d3,.stepyRight
        bra .finished
.stepyRight:
        move.w d4,d0
        add.w d0,d0
        cmp.w d2,d0
        blt.s .noXyRight
        add.w d2,d4
        ror.l #1,d5
        bcc.s .noXyRight
        addq.l #8,a0
.noXyRight:
        add.w d1,d4
        adda.w d7,a0
        bra .yRight
.yLeft:
        move.l d5,d6
        mWhiteFlush
        dbra d3,.stepyLeft
        bra .finished
.stepyLeft:
        move.w d4,d0
        add.w d0,d0
        cmp.w d2,d0
        blt.s .noXyLeft
        add.w d2,d4
        rol.l #1,d5
        bcc.s .noXyLeft
        subq.l #8,a0
.noXyLeft:
        add.w d1,d4
        adda.w d7,a0
        bra .yLeft
.last:
        mWhiteFlush
.finished:
        move.l a3,gIrisLogEnd
        movem.l (sp)+,d2-d7/a2-a6
        rts
Iris_WhiteLineEnd:
        xdef Iris_CopyRows,Iris_CopyRowsEnd
Iris_CopyRows:
; Copy only image planes 0..2; preserve live shutter in plane 3.
; a0 dest,a1 clean image,d0 first row,d1 row count. 50 rows per page update.
        movem.l d2,-(sp)
        mulu.w #160,d0
        adda.l d0,a0
        adda.l d0,a1
        subq.w #1,d1
.rowCopy:
copyOffset set 0
        rept 20
        move.l copyOffset(a1),copyOffset(a0)
        move.w copyOffset+4(a1),copyOffset+4(a0)
copyOffset set copyOffset+8
        endr
        lea 160(a0),a0
        lea 160(a1),a1
        dbra d1,.rowCopy
        movem.l (sp)+,d2
        rts
Iris_CopyRowsEnd:
        section data
        even
Iris_Edges:
; x=0..320: tail mask, interleaved-word byte offset (1284 bytes).
        dc.w $ffff,0
        dc.w $7fff,0
        dc.w $3fff,0
        dc.w $1fff,0
        dc.w $0fff,0
        dc.w $07ff,0
        dc.w $03ff,0
        dc.w $01ff,0
        dc.w $00ff,0
        dc.w $007f,0
        dc.w $003f,0
        dc.w $001f,0
        dc.w $000f,0
        dc.w $0007,0
        dc.w $0003,0
        dc.w $0001,0
        dc.w $ffff,8
        dc.w $7fff,8
        dc.w $3fff,8
        dc.w $1fff,8
        dc.w $0fff,8
        dc.w $07ff,8
        dc.w $03ff,8
        dc.w $01ff,8
        dc.w $00ff,8
        dc.w $007f,8
        dc.w $003f,8
        dc.w $001f,8
        dc.w $000f,8
        dc.w $0007,8
        dc.w $0003,8
        dc.w $0001,8
        dc.w $ffff,16
        dc.w $7fff,16
        dc.w $3fff,16
        dc.w $1fff,16
        dc.w $0fff,16
        dc.w $07ff,16
        dc.w $03ff,16
        dc.w $01ff,16
        dc.w $00ff,16
        dc.w $007f,16
        dc.w $003f,16
        dc.w $001f,16
        dc.w $000f,16
        dc.w $0007,16
        dc.w $0003,16
        dc.w $0001,16
        dc.w $ffff,24
        dc.w $7fff,24
        dc.w $3fff,24
        dc.w $1fff,24
        dc.w $0fff,24
        dc.w $07ff,24
        dc.w $03ff,24
        dc.w $01ff,24
        dc.w $00ff,24
        dc.w $007f,24
        dc.w $003f,24
        dc.w $001f,24
        dc.w $000f,24
        dc.w $0007,24
        dc.w $0003,24
        dc.w $0001,24
        dc.w $ffff,32
        dc.w $7fff,32
        dc.w $3fff,32
        dc.w $1fff,32
        dc.w $0fff,32
        dc.w $07ff,32
        dc.w $03ff,32
        dc.w $01ff,32
        dc.w $00ff,32
        dc.w $007f,32
        dc.w $003f,32
        dc.w $001f,32
        dc.w $000f,32
        dc.w $0007,32
        dc.w $0003,32
        dc.w $0001,32
        dc.w $ffff,40
        dc.w $7fff,40
        dc.w $3fff,40
        dc.w $1fff,40
        dc.w $0fff,40
        dc.w $07ff,40
        dc.w $03ff,40
        dc.w $01ff,40
        dc.w $00ff,40
        dc.w $007f,40
        dc.w $003f,40
        dc.w $001f,40
        dc.w $000f,40
        dc.w $0007,40
        dc.w $0003,40
        dc.w $0001,40
        dc.w $ffff,48
        dc.w $7fff,48
        dc.w $3fff,48
        dc.w $1fff,48
        dc.w $0fff,48
        dc.w $07ff,48
        dc.w $03ff,48
        dc.w $01ff,48
        dc.w $00ff,48
        dc.w $007f,48
        dc.w $003f,48
        dc.w $001f,48
        dc.w $000f,48
        dc.w $0007,48
        dc.w $0003,48
        dc.w $0001,48
        dc.w $ffff,56
        dc.w $7fff,56
        dc.w $3fff,56
        dc.w $1fff,56
        dc.w $0fff,56
        dc.w $07ff,56
        dc.w $03ff,56
        dc.w $01ff,56
        dc.w $00ff,56
        dc.w $007f,56
        dc.w $003f,56
        dc.w $001f,56
        dc.w $000f,56
        dc.w $0007,56
        dc.w $0003,56
        dc.w $0001,56
        dc.w $ffff,64
        dc.w $7fff,64
        dc.w $3fff,64
        dc.w $1fff,64
        dc.w $0fff,64
        dc.w $07ff,64
        dc.w $03ff,64
        dc.w $01ff,64
        dc.w $00ff,64
        dc.w $007f,64
        dc.w $003f,64
        dc.w $001f,64
        dc.w $000f,64
        dc.w $0007,64
        dc.w $0003,64
        dc.w $0001,64
        dc.w $ffff,72
        dc.w $7fff,72
        dc.w $3fff,72
        dc.w $1fff,72
        dc.w $0fff,72
        dc.w $07ff,72
        dc.w $03ff,72
        dc.w $01ff,72
        dc.w $00ff,72
        dc.w $007f,72
        dc.w $003f,72
        dc.w $001f,72
        dc.w $000f,72
        dc.w $0007,72
        dc.w $0003,72
        dc.w $0001,72
        dc.w $ffff,80
        dc.w $7fff,80
        dc.w $3fff,80
        dc.w $1fff,80
        dc.w $0fff,80
        dc.w $07ff,80
        dc.w $03ff,80
        dc.w $01ff,80
        dc.w $00ff,80
        dc.w $007f,80
        dc.w $003f,80
        dc.w $001f,80
        dc.w $000f,80
        dc.w $0007,80
        dc.w $0003,80
        dc.w $0001,80
        dc.w $ffff,88
        dc.w $7fff,88
        dc.w $3fff,88
        dc.w $1fff,88
        dc.w $0fff,88
        dc.w $07ff,88
        dc.w $03ff,88
        dc.w $01ff,88
        dc.w $00ff,88
        dc.w $007f,88
        dc.w $003f,88
        dc.w $001f,88
        dc.w $000f,88
        dc.w $0007,88
        dc.w $0003,88
        dc.w $0001,88
        dc.w $ffff,96
        dc.w $7fff,96
        dc.w $3fff,96
        dc.w $1fff,96
        dc.w $0fff,96
        dc.w $07ff,96
        dc.w $03ff,96
        dc.w $01ff,96
        dc.w $00ff,96
        dc.w $007f,96
        dc.w $003f,96
        dc.w $001f,96
        dc.w $000f,96
        dc.w $0007,96
        dc.w $0003,96
        dc.w $0001,96
        dc.w $ffff,104
        dc.w $7fff,104
        dc.w $3fff,104
        dc.w $1fff,104
        dc.w $0fff,104
        dc.w $07ff,104
        dc.w $03ff,104
        dc.w $01ff,104
        dc.w $00ff,104
        dc.w $007f,104
        dc.w $003f,104
        dc.w $001f,104
        dc.w $000f,104
        dc.w $0007,104
        dc.w $0003,104
        dc.w $0001,104
        dc.w $ffff,112
        dc.w $7fff,112
        dc.w $3fff,112
        dc.w $1fff,112
        dc.w $0fff,112
        dc.w $07ff,112
        dc.w $03ff,112
        dc.w $01ff,112
        dc.w $00ff,112
        dc.w $007f,112
        dc.w $003f,112
        dc.w $001f,112
        dc.w $000f,112
        dc.w $0007,112
        dc.w $0003,112
        dc.w $0001,112
        dc.w $ffff,120
        dc.w $7fff,120
        dc.w $3fff,120
        dc.w $1fff,120
        dc.w $0fff,120
        dc.w $07ff,120
        dc.w $03ff,120
        dc.w $01ff,120
        dc.w $00ff,120
        dc.w $007f,120
        dc.w $003f,120
        dc.w $001f,120
        dc.w $000f,120
        dc.w $0007,120
        dc.w $0003,120
        dc.w $0001,120
        dc.w $ffff,128
        dc.w $7fff,128
        dc.w $3fff,128
        dc.w $1fff,128
        dc.w $0fff,128
        dc.w $07ff,128
        dc.w $03ff,128
        dc.w $01ff,128
        dc.w $00ff,128
        dc.w $007f,128
        dc.w $003f,128
        dc.w $001f,128
        dc.w $000f,128
        dc.w $0007,128
        dc.w $0003,128
        dc.w $0001,128
        dc.w $ffff,136
        dc.w $7fff,136
        dc.w $3fff,136
        dc.w $1fff,136
        dc.w $0fff,136
        dc.w $07ff,136
        dc.w $03ff,136
        dc.w $01ff,136
        dc.w $00ff,136
        dc.w $007f,136
        dc.w $003f,136
        dc.w $001f,136
        dc.w $000f,136
        dc.w $0007,136
        dc.w $0003,136
        dc.w $0001,136
        dc.w $ffff,144
        dc.w $7fff,144
        dc.w $3fff,144
        dc.w $1fff,144
        dc.w $0fff,144
        dc.w $07ff,144
        dc.w $03ff,144
        dc.w $01ff,144
        dc.w $00ff,144
        dc.w $007f,144
        dc.w $003f,144
        dc.w $001f,144
        dc.w $000f,144
        dc.w $0007,144
        dc.w $0003,144
        dc.w $0001,144
        dc.w $ffff,152
        dc.w $7fff,152
        dc.w $3fff,152
        dc.w $1fff,152
        dc.w $0fff,152
        dc.w $07ff,152
        dc.w $03ff,152
        dc.w $01ff,152
        dc.w $00ff,152
        dc.w $007f,152
        dc.w $003f,152
        dc.w $001f,152
        dc.w $000f,152
        dc.w $0007,152
        dc.w $0003,152
        dc.w $0001,152
        dc.w $ffff,160
