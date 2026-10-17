; FLAGWAVE: 20 word-aligned 16px columns, CPU only, 68000 / ST / STE.
; Immutable column-major source (no preshifts, duplicated pixels or codegen).
        section text
        xdef Flag_Prepare,Flag_PrepareEnd,Flag_Draw,Flag_DrawEnd
        xdef Flag_MouseShift,Flag_MouseShiftEnd,Flag_CopyColumn,Flag_SkipColumn
        xref gFlagMode,gFlagPhase,gFlagSine,gFlagFrameOffsets
        xref gFlagMouseOffsets,gFlagMouseInput,gFlagScreen,gFlagOldOffsets
Flag_Prepare:
        movem.l d2-d3,-(sp)
        lea gFlagFrameOffsets,a0
        tst.w gFlagMode
        beq.s Flag_PrepareMouse
        move.l gFlagSine,a1
        move.w gFlagPhase,d0
        add.w #228,d0
        moveq #19,d3
Flag_PrepareAuto:
        and.w #255,d0
        move.w d0,d1
        add.w d1,d1
        move.w (a1,d1.w),(a0)+
        sub.w #12,d0
        dbra d3,Flag_PrepareAuto
        bra.s Flag_PrepareDone
Flag_PrepareMouse:
        lea gFlagMouseOffsets,a1
        moveq #9,d3
Flag_PrepareMouseCopy:
        move.l (a1)+,(a0)+
        dbra d3,Flag_PrepareMouseCopy
Flag_PrepareDone:
        movem.l (sp)+,d2-d3
        rts
Flag_PrepareEnd:

Flag_MouseShift:
        lea gFlagMouseOffsets,a0
        lea 2(a0),a1
        rept 10
        move.l (a1)+,(a0)+
        endr
        move.w gFlagMouseInput,(a0)
        rts
Flag_MouseShiftEnd:

Flag_Draw:
        movem.l d2-d7/a2-a6,-(sp)
        lea Flag_Columns,a3
        move.l gFlagScreen,a4
        lea gFlagFrameOffsets,a5
        move.l gFlagOldOffsets,a6
        moveq #19,d7
Flag_Column:
        move.w (a5)+,d0
        cmp.w (a6),d0
        beq Flag_SkipColumn
        move.w d0,(a6)
Flag_CopyColumn:
        move.l a3,a0
        move.l a4,a1
        move.w d0,d1
        bpl.s Flag_Positive
        neg.w d1
; Negative dy: skip source rows and compensate destination displacement.
        move.w d1,d2
        lsl.w #3,d2
        adda.w d2,a0
        move.w d1,d3
        lsl.w #5,d3
        move.w d1,d2
        lsl.w #7,d2
        add.w d3,d2 ; dy*160
        suba.w d2,a1
Flag_Positive:
; Each generated-by-REPT row is exactly 8 code bytes. Jump over clipped rows.
        move.w d1,d2
        lsl.w #3,d2
        lea Flag_CopyRows(pc),a2
        adda.w d2,a2
        jsr (a2)
; Clear only the newly uncovered edge of this column, not the full screen.
        tst.w d1
        beq.s Flag_NextColumn
        move.l a4,a1
        tst.w d0
        bpl.s Flag_ClearTop
        move.w #200,d2
        sub.w d1,d2
        move.w d2,d3
        lsl.w #7,d2
        lsl.w #5,d3
        add.w d3,d2
        adda.w d2,a1
Flag_ClearTop:
        moveq #0,d2
        subq.w #1,d1
Flag_ClearRows:
        move.l d2,(a1)
        move.l d2,4(a1)
        lea 160(a1),a1
        dbra d1,Flag_ClearRows
Flag_SkipColumn:
Flag_NextColumn:
        addq.l #2,a6
        adda.w #1600,a3
        addq.l #8,a4
        dbra d7,Flag_Column
        movem.l (sp)+,d2-d7/a2-a6
        rts
; Do not let zero-displacement optimisation change the jump stride.
        opt o-
Flag_CopyRows:
Y       set 0
        rept 200
        move.l (a0)+,Y*160(a1)
        move.l (a0)+,Y*160+4(a1)
Y       set Y+1
        endr
Flag_CopyRowsEnd:
        ifne Flag_CopyRowsEnd-Flag_CopyRows-1600
        fail 'FLAGWAVE row copy must use exactly eight code bytes per row'
        endc
        rts
Flag_DrawEnd:
        section data
        even
        xdef Flag_Palette,Flag_Columns,Flag_Sine
Flag_Palette:
        incbin 'assets/PALETTE.BIN'
Flag_Columns:
        incbin 'assets/COLUMNS.BIN'
Flag_Sine:
        incbin 'assets/SINE.BIN'
