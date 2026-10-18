; Exact envelope of six original Q4 half planes; C supplies <=5 active runs.
; a0 200 spans, a1 {xL,xR,dxL,dxR,count}; d0 first.
; count<0: empty run; bit 14: full run; zero: end.
        section text
        xref gIrisSpans
        xdef Iris_Scan,Iris_ScanEnd
Iris_Scan:
        movem.l d2-d6/a2,-(sp)
        move.w d0,d1
        beq.s .run
        subq.w #1,d1
.prefix:
        move.l #$0000ffff,(a0)+
        dbra d1,.prefix
.run:
        movem.l (a1)+,d2-d5
        move.w (a1)+,d6
        beq .tail
        bmi .emptyRun
        btst #14,d6
        bne .fullRun
        subq.w #1,d6
.row:
        move.l d2,d0
        move.l d3,d1
        swap d0
        swap d1
        add.w #160,d0
        add.w #160,d1
        tst.w d0
        bge.s .left
        moveq #0,d0
.left:  cmp.w #319,d1
        ble.s .right
        move.w #319,d1
.right: cmp.w d0,d1
        bge.s .valid
        moveq #0,d0
        moveq #-1,d1
.valid: move.w d0,(a0)+
        move.w d1,(a0)+
        add.l d4,d2
        add.l d5,d3
        dbra d6,.row
        bra.s .run
.emptyRun:
        neg.w d6
        subq.w #1,d6
.emptyLoop:
        move.l #$0000ffff,(a0)+
        dbra d6,.emptyLoop
        bra .run
.fullRun:
        and.w #$3fff,d6
        subq.w #1,d6
.fullLoop:
        move.l #$0000013f,(a0)+
        dbra d6,.fullLoop
        bra .run
.tail:
        lea gIrisSpans+800,a2
.endRows:
        cmpa.l a2,a0
        bge.s .done
        move.l #$0000ffff,(a0)+
        bra.s .endRows
.done:  movem.l (sp)+,d2-d6/a2
        rts
Iris_ScanEnd:
