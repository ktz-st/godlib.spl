; Live differential wedges: compute intersections, XOR only changed ray spans.
; a0 screen, a1 per-page history (inverse,phase,200*3 mask/offset longs), d0 phase,d1 inverse.
; History contains packed edge masks/offsets, never image data. Initially each
; edge record is $ffff0000 (x=0), headers and plane 2 are zero. Other planes stay intact.
        section text
        MACRO mWedgesXorSpan
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
        addq.l #8,a0
        lsr.w #3,d2
        subq.w #2,d2
        bmi.s .right\@
.middle\@:
        not.w (a0)
        addq.l #8,a0
        dbra d2,.middle\@
.right\@:
        swap d1
        not.w d1
        beq.s .xorReturn\@
        eor.w d1,(a0)
        bra.s .xorReturn\@
.sameWord\@:
        move.l a6,a0
        adda.w d0,a0
        eor.l d1,d0
        swap d0
        beq.s .xorReturn\@
        eor.w d0,(a0)
.xorReturn\@:
        ENDM
        xdef Wedges_Live,Wedges_LiveEnd
Wedges_Live:
        movem.l d2-d7/a2-a6,-(sp)
        lea -16(sp),sp           ; 3 long row steps, half flag, wrap mode
        moveq #0,d3
        move.w (a1),d2
        eor.w d1,d2
        beq.s .mode
        moveq #1,d3             ; forward sector wrap
        cmp.w 2(a1),d0
        blt.s .mode
        moveq #2,d3             ; backward wrap (also valid for arbitrary jumps)
.mode:
        move.w d3,14(sp)
        move.w d1,(a1)
        move.w d0,2(a1)
        addq.l #4,a1
        add.w d0,d0
        move.w d0,d2
        add.w d0,d0
        add.w d2,d0
        lea Wedges_LiveCots,a2
        adda.w d0,a2
; Q16 instead of Q9: SWAP extracts floor(x) without three long shifts per row.
        move.w 4(a2),d4
        move.w d4,d0
        ext.l d0
        lsl.l #8,d0
        move.l d0,(sp)
        muls.w #-199,d4
        lsl.l #7,d4
        add.l #10485760,d4
        move.w 2(a2),d5
        move.w d5,d0
        ext.l d0
        lsl.l #8,d0
        move.l d0,4(sp)
        muls.w #-199,d5
        lsl.l #7,d5
        add.l #10485760,d5
        move.w (a2),d6
        move.w d6,d0
        ext.l d0
        lsl.l #8,d0
        move.l d0,8(sp)
        muls.w #-199,d6
        lsl.l #7,d6
        add.l #10485760,d6
        move.w #1,12(sp)
        adda.w #4,a0
        lea Wedges_LiveXMasks,a2
        bra.s .half
.dispatchTable:
        dc.w 0,.forward-.normal,.backward-.normal
.half:
        move.w 14(sp),d3
        add.w d3,d3
        move.w .dispatchTable(pc,d3.w),d3
        move.w #99,d7
.row:
        move.l d4,d0
        swap d0
        move.l d5,d1
        swap d1
        move.l d6,d2
        swap d2
        add.l (sp),d4
        add.l 4(sp),d5
        add.l 8(sp),d6
; Sorted lines: the median always lies inside the viewport. Only L's
; minimum and R's maximum need clamping (proven for every COTS.S entry).
        tst.w d0
        bge.s .lReady
        moveq #0,d0
.lReady:
        cmp.w #320,d2
        ble.s .rReady
        move.w #320,d2
.rReady:
        movem.l (a1),a3-a5      ; previous packed mask/offset records
        add.w d0,d0
        add.w d0,d0
        add.w d1,d1
        add.w d1,d1
        add.w d2,d2
        add.w d2,d2
        move.l (a2,d0.w),(a1)+
        move.l (a2,d1.w),(a1)+
        move.l (a2,d2.w),(a1)+
        move.l a0,a6            ; row base survives the XOR span calls
        jmp .normal(pc,d3.w)
.normal:
        move.l a3,d0
        move.l -12(a1),d1
        mWedgesXorSpan
        move.l a4,d0
        move.l -8(a1),d1
        mWedgesXorSpan
        move.l a5,d0
        move.l -4(a1),d1
        mWedgesXorSpan
        bra .rowDone
.forward:
; At a sector wrap, match the nearby rays cyclically. The third pair is
; complemented, cancelling the global inversion without scanning the plane.
        move.l a3,d0
        move.l -8(a1),d1
        mWedgesXorSpan
        move.l a4,d0
        move.l -4(a1),d1
        mWedgesXorSpan
        move.l a5,d0
        move.l -12(a1),d1
        bra .complement
.backward:
        move.l a4,d0
        move.l -12(a1),d1
        mWedgesXorSpan
        move.l a5,d0
        move.l -8(a1),d1
        mWedgesXorSpan
        move.l a3,d0
        move.l -4(a1),d1
.complement:
        cmp.w d0,d1
        bge.s .ordered
        exg d0,d1
.ordered:
; The near-vertical ray is clipped at both edges in almost every row.
; Its complemented interval is empty: skip both edge calls completely.
        cmp.l #$ffff0000,d0
        bne.s .edgeComplement
        cmp.l #$ffff00a0,d1
        beq .rowDone
.edgeComplement:
        move.l d1,-(sp)         ; max endpoint
        move.l d0,d1           ; [0,min)
        move.l #$ffff0000,d0
        mWedgesXorSpan
        move.l (sp)+,d0        ; [max,320)
        move.l #$ffff00a0,d1
        mWedgesXorSpan
.rowDone:
        lea 160(a6),a0
        dbra d7,.row
        tst.w 12(sp)
        beq.s .done
        clr.w 12(sp)
; The sorted coordinate order reverses below the centre. Reverse the cyclic
; ray correspondence too, otherwise equivalent XOR intervals overlap across
; most of the lower half at sector wraps (correct pixels, wasteful redraw).
        tst.w 14(sp)
        beq.s .sameMode
        eori.w #3,14(sp)
.sameMode:
        exg d4,d6
        move.l (sp),d0
        move.l 8(sp),d1
        move.l d1,(sp)
        move.l d0,8(sp)
        bra .half
.done:
        lea 16(sp),sp
        movem.l (sp)+,d2-d7/a2-a6
        rts
Wedges_LiveEnd:
        section data
        even
        xdef Wedges_LiveTables,Wedges_LiveTablesEnd
Wedges_LiveTables:
Wedges_LiveCots:
        include 'assets/COTS.S'
Wedges_LiveXMasks:
        include 'assets/XMASKS.S'
Wedges_LiveTablesEnd:
