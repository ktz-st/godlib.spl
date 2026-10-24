; DCK route-switching scroller adaptation, 68000 / four planes / stride 160.
; FE P/H/V, FE 0..9 and FF retain the DCK command encoding.
; New: shared glyph queue, live path interpolation and per-page exposed-edge erase.
        section text
        xdef Route_Init,Route_Frame,Route_Advance,Route_Erase,Route_Draw
        xdef Route_RuntimeEnd,Route_Columns,Route_Rows,Route_Palette,Route_Paths,Route_Text
        xref gRouteScreen,gRoutePage,gRouteMode,gRouteProfile,gRoutePhase
        xref gRouteQueue,gRouteY,gRoutePreviousY,gRoutePreviousMode,gRouteColumnPtrs
        xref gRouteText,gRouteCommands,gRouteRequest
Route_Init:
        movem.l d0-d7/a0-a6,-(sp)
        move.l #Route_Text,gRouteText
        clr.w gRouteMode
        move.w #2,gRouteProfile
        clr.w gRoutePhase
        move.l #$ffffffff,gRoutePreviousMode
        lea gRouteQueue,a5
        moveq #8,d7
.prime: bsr Route_NextGlyph
        move.w d0,(a5)+
        dbf d7,.prime
        lea Route_Paths+160,a0
        lea gRouteY,a1
        moveq #39,d7
.path:  move.w (a0)+,(a1)+
        dbf d7,.path
        movem.l (sp)+,d0-d7/a0-a6
        rts
; Called once per glyph boundary, including the initial nine-glyph lookahead.
; FE commands affect the entire queued text. Never reset queue or scroll phase.
Route_NextGlyph:
        move.l gRouteText,a0
.again: moveq #0,d0
        move.b (a0)+,d0
        cmpi.b #255,d0
        beq.s .wrap
        cmpi.b #254,d0
        beq.s .command
        move.l a0,gRouteText
        rts
.wrap:  lea Route_Text,a0
        bra.s .again
.command:
        addq.l #1,gRouteCommands
        moveq #0,d0
        move.b (a0)+,d0
        cmpi.b #'P',d0
        beq.s .p
        cmpi.b #'H',d0
        beq.s .h
        cmpi.b #'V',d0
        beq.s .v
        subi.w #'0',d0
        cmpi.w #9,d0
        bhi.s .again
        move.w d0,gRouteProfile
        bra.s .again
.p:     clr.w gRouteMode
        bra.s .again
.h:     move.w #1,gRouteMode
        bra.s .again
.v:     move.w #2,gRouteMode
        bra.s .again
Route_Frame:
        bsr Route_Erase
        bsr Route_Draw
        rts
Route_Advance:
        movem.l d0-d7/a0-a6,-(sp)
        moveq #8,d0
        cmpi.w #2,gRouteMode
        bne.s .step
        moveq #1,d0
.step:  add.w d0,gRoutePhase
        cmpi.w #40,gRoutePhase
        blo.s .morph
        clr.w gRoutePhase
        lea gRouteQueue,a1
        moveq #7,d7
.shift: move.w 2(a1),(a1)+
        dbf d7,.shift
        bsr Route_NextGlyph
        move.w d0,gRouteQueue+16
        move.w gRouteRequest,d0
        beq.s .morph
        clr.w gRouteRequest
        subq.w #1,d0
        cmpi.w #9,d0
        bhi.s .mode
        move.w d0,gRouteProfile
        clr.w gRouteMode
        bra.s .morph
.mode:  subi.w #9,d0           ; request 11 -> H=1, request 12 -> V=2
        move.w d0,gRouteMode
.morph:
        cmpi.w #2,gRouteMode
        beq.s .done
        move.w gRouteProfile,d0
        mulu.w #80,d0
        lea Route_Paths,a0
        adda.w d0,a0
        lea gRouteY,a1
        moveq #39,d7
.y:     move.w (a0)+,d0
        tst.w gRouteMode
        beq.s .target
        moveq #84,d0
.target:
        cmp.w (a1),d0
        beq.s .same
        blt.s .up
        addq.w #1,(a1)
        bra.s .same
.up:    subq.w #1,(a1)
.same:  addq.l #2,a1
        dbf d7,.y
.done:  movem.l (sp)+,d0-d7/a0-a6
        rts
; Remove only the exposed edge of each old 8x32 strip when P/H moves.
; A P/H <-> V change removes the complete old footprint, once on each page.
Route_Erase:
        movem.l d0-d7/a0-a6,-(sp)
        move.w gRoutePage,d0
        add.w d0,d0
        lea gRoutePreviousMode,a0
        move.w 0(a0,d0.w),d6
        bmi .done
        cmpi.w #2,d6
        bne.s .strips
        cmpi.w #2,gRouteMode
        beq .done
        move.l gRouteScreen,a1
        lea 3912(a1),a1
        moveq #0,d0
        moveq #0,d1
        moveq #0,d2
        moveq #0,d3
        moveq #0,d4
        move.w #159,d7
.vclear:
        movem.l d0-d3,(a1)
        movep.l d4,16(a1)
        lea 160(a1),a1
        dbf d7,.vclear
        bra .done
.strips:
        move.w gRoutePage,d0
        mulu.w #80,d0
        lea gRoutePreviousY,a3
        adda.w d0,a3
        lea gRouteY,a4
        moveq #0,d4            ; destination byte offset (0,1,8,9,...)
        moveq #0,d5            ; slice number
        moveq #39,d7
.col:   move.w (a3)+,d0        ; old Y
        move.w (a4)+,d1        ; new Y
        moveq #32,d2
        cmpi.w #2,gRouteMode
        beq.s .clear
        sub.w d0,d1           ; delta = new - old
        beq.s .next
        bmi.s .rising
        cmp.w d2,d1
        bge.s .clear
        move.w d1,d2          ; clear old top
        bra.s .clear
.rising:
        neg.w d1
        cmp.w d2,d1
        bge.s .clear
        add.w d2,d0
        sub.w d1,d0           ; clear old bottom
        move.w d1,d2
.clear: mulu.w #160,d0
        add.w d4,d0
        move.l gRouteScreen,a1
        adda.w d0,a1
        moveq #0,d0
        subq.w #1,d2
.rows:  movep.l d0,0(a1)
        lea 160(a1),a1
        dbf d2,.rows
.next:  addq.w #1,d5
        addq.w #1,d4
        btst #0,d5
        bne.s .byte
        addq.w #6,d4
.byte:  dbf d7,.col
.done:  movem.l (sp)+,d0-d7/a0-a6
        rts
Route_Draw:
        movem.l d0-d7/a0-a6,-(sp)
        move.w gRoutePage,d0
        add.w d0,d0
        lea gRoutePreviousMode,a0
        move.w gRouteMode,0(a0,d0.w)
        cmpi.w #2,gRouteMode
        beq .vertical
        ; Resolve 9 glyphs into 45 pointers, then select a 40-column window.
        lea gRouteQueue,a3
        lea gRouteColumnPtrs,a2
        lea Route_ColumnGlyphs,a4
        moveq #8,d7
.ptr:   moveq #0,d0
        move.w (a3)+,d0
        lsl.w #2,d0
        move.l 0(a4,d0.w),a0
        rept 5
        move.l a0,(a2)+
        lea 128(a0),a0
        endr
        dbf d7,.ptr
        move.w gRoutePage,d0
        mulu.w #80,d0
        lea gRoutePreviousY,a3
        adda.w d0,a3
        lea gRouteY,a4
        lea gRouteColumnPtrs,a2
        move.w gRoutePhase,d0
        lsr.w #3,d0
        lsl.w #2,d0
        adda.w d0,a2
        moveq #0,d4
        moveq #0,d5
        moveq #39,d7
.col:   move.w (a4)+,d0
        move.w d0,(a3)+
        mulu.w #160,d0
        add.w d4,d0
        move.l gRouteScreen,a1
        adda.w d0,a1
        move.l (a2)+,a0
OFF     set 0
        rept 32
        move.l (a0)+,d0
        movep.l d0,OFF(a1)
OFF     set OFF+160
        endr
        addq.w #1,d5
        addq.w #1,d4
        btst #0,d5
        bne.s .byte
        addq.w #6,d4
.byte:  dbf d7,.col
        bra.s .done
.vertical:
        lea gRouteQueue,a3
        lea Route_RowGlyphs,a2
        move.w (a3)+,d0
        lsl.w #2,d0
        move.l 0(a2,d0.w),a0
        move.w gRoutePhase,d7
        move.w d7,d0
        mulu.w #20,d0
        adda.w d0,a0
        move.l gRouteScreen,a1
        lea 3912(a1),a1         ; X144, Y24, 40x160
        move.w #159,d6
.row:   cmpi.w #32,d7
        bhs.s .blank
        movem.l (a0)+,d0-d4
        bra.s .put
.blank: moveq #0,d0
        moveq #0,d1
        moveq #0,d2
        moveq #0,d3
        moveq #0,d4
.put:   movem.l d0-d3,(a1)
        movep.l d4,16(a1)
        lea 160(a1),a1
        addq.w #1,d7
        cmpi.w #40,d7
        bne.s .continue
        clr.w d7
        move.w (a3)+,d0
        lsl.w #2,d0
        move.l 0(a2,d0.w),a0
.continue:
        dbf d6,.row
.done:  movem.l (sp)+,d0-d7/a0-a6
        rts
Route_RuntimeEnd:
        section data
        include "assets/text.inc"
Route_Columns: incbin "assets/COLUMNS.BIN"
Route_Rows:    incbin "assets/ROWS.BIN"
Route_Palette: incbin "assets/PALETTE.BIN"
Route_Paths:   incbin "assets/PATHS.BIN"
        even
