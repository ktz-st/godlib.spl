; LCK-inspired bitmap transitions, 320x160 4-plane stage at screen Y=24.
; All per-pixel work is 68000 word/longword ASM; there is no frame cache.
        section text
        xdef Lw_Begin,Lw_Render,Lw_RenderEnd,Lw_Show,Lw_ShowEnd
        xdef Lw_Spiral,Lw_SpiralEnd,Lw_Fold,Lw_FoldEnd
        xdef Lw_Lines,Lw_LinesEnd,Lw_Snake,Lw_SnakeEnd
        xdef Lw_Instant,Lw_InstantEnd,Lw_Colours,Lw_ColoursEnd
        xdef Lw_Centre,Lw_CentreEnd,Lw_Smear,Lw_SmearEnd
        xdef Lw_InterRows,Lw_InterRowsEnd,Lw_CurtainCols,Lw_CurtainColsEnd,Lw_InterCols,Lw_InterColsEnd
        xdef Lw_RowList,Lw_RowListEnd,Lw_Columns,Lw_ColumnsEnd,Lw_Full,Lw_FullEnd,Lw_PaletteSelect,Lw_PaletteSelectEnd
        xref gLwDest,gLwSource,gLwRows,gLwOld,gLwPrevious,gLwRowHistory
        xref gLwEffect,gLwTarget,gLwClosing
        xref gLwColMasks,gLwStages,gLwNextPalette
Lw_Begin:
        cmpi.w #5,gLwEffect
        bne.s .history
        bsr.w Lw_PaletteSelect
.history:
        clr.l gLwPrevious
        lea gLwRowHistory,a0
        tst.w gLwClosing
        beq.s .black
        lea Lw_RowOffsets,a1
        move.w #159,d0
.full:  move.w (a1)+,d1
        move.w d1,320(a0)
        move.w d1,(a0)+
        dbf d0,.full
        rts
.black: moveq #-1,d1
        move.w #319,d0
.clear: move.w d1,(a0)+
        dbf d0,.clear
        rts
Lw_Render:
        move.w gLwEffect,d0
        lsl.w #2,d0
        lea .vectors(pc),a0
        jmp 0(a0,d0.w)
.vectors:
        bra.w Lw_Spiral
        bra.w Lw_Fold
        bra.w Lw_Lines
        bra.w Lw_Snake
        bra.w Lw_Instant
        bra.w Lw_Colours
        bra.w Lw_Centre
        bra.w Lw_Smear
        bra.w Lw_InterRows
        bra.w Lw_CurtainCols
        bra.w Lw_InterCols
Lw_RenderEnd:
Lw_Spiral:
        movem.l d2-d7/a2-a6,-(sp)
        move.l gLwOld,a0
        move.w (a0),d0
        move.w gLwTarget,d7
        cmp.w d0,d7
        beq.w .done
        move.w d7,(a0)
        sub.w d0,d7
        subq.w #1,d7
        add.w d0,d0
        lea Lw_SpiralOffsets,a4
        adda.w d0,a4
        move.l gLwDest,a2
        move.l gLwSource,a3
        tst.w gLwClosing
        beq.s .copy
        moveq #0,d0
.erase: move.w (a4)+,d1
        lea 0(a2,d1.w),a1
Y       set 0
        rept 8
        movep.l d0,Y(a1)
Y       set Y+160
        endr
        dbf d7,.erase
        bra.s .done
.copy:  move.w (a4)+,d1
        lea 0(a2,d1.w),a1
        lea 0(a3,d1.w),a0
Y       set 0
        rept 8
        movep.l Y(a0),d0
        movep.l d0,Y(a1)
Y       set Y+160
        endr
        dbf d7,.copy
.done:  movem.l (sp)+,d2-d7/a2-a6
        rts
Lw_SpiralEnd:
Lw_Snake:
        movem.l d2-d7/a2-a6,-(sp)
        move.l gLwOld,a0
        move.w (a0),d0
        move.w gLwTarget,d7
        cmp.w d0,d7
        beq.w .done
        move.w d7,(a0)
        sub.w d0,d7
        subq.w #1,d7
        add.w d0,d0
        lea Lw_SnakeOffsets,a4
        adda.w d0,a4
        move.l gLwDest,a2
        move.l gLwSource,a3
        tst.w gLwClosing
        beq.s .copy
.erase: move.w (a4)+,d1
        lea 0(a2,d1.w),a1
Y       set 0
        rept 10
        clr.l Y(a1)
        clr.l Y+4(a1)
Y       set Y+160
        endr
        dbf d7,.erase
        bra.w .done
.copy:  move.w (a4)+,d1
        lea 0(a2,d1.w),a1
        lea 0(a3,d1.w),a0
Y       set 0
        rept 10
        move.l Y(a0),Y(a1)
        move.l Y+4(a0),Y+4(a1)
Y       set Y+160
        endr
        dbf d7,.copy
.done:  movem.l (sp)+,d2-d7/a2-a6
        rts
Lw_SnakeEnd:
Lw_Lines:
        movem.l d2-d7/a2-a6,-(sp)
        move.l gLwOld,a0
        move.w (a0),d0
        move.w gLwTarget,d1
        cmp.w d0,d1
        beq.w .done
        move.w d1,(a0)
        move.w d1,d3
        sub.w d0,d3              ; newly exposed 16px columns
        lsl.w #3,d0              ; left start in bytes
        move.w #20,d2
        sub.w d1,d2
        lsl.w #3,d2
        addi.w #160,d2           ; right start on the odd rows
        lsl.w #3,d3              ; span bytes
        move.w #320,d4
        sub.w d3,d4              ; next row of the same parity
        move.w d3,d5
        lsr.w #1,d5              ; code size: span/4 longs * 2 bytes
        moveq #1,d7
.parity:
        move.l gLwDest,a1
        adda.w d0,a1
        move.l gLwSource,a0
        adda.w d0,a0
        moveq #79,d6
        tst.w gLwClosing
        bne.s .black
        lea .copyend(pc),a6
        suba.w d5,a6
.rowcopy:
        jmp (a6)
        rept 40
        move.l (a0)+,(a1)+
        endr
.copyend:
        adda.w d4,a0
        adda.w d4,a1
        dbf d6,.rowcopy
        bra.s .next
.black: lea .clearend(pc),a6
        suba.w d5,a6
.rowclear:
        jmp (a6)
        rept 40
        clr.l (a1)+
        endr
.clearend:
        adda.w d4,a1
        dbf d6,.rowclear
.next:  move.w d2,d0
        dbf d7,.parity
.done:  movem.l (sp)+,d2-d7/a2-a6
        rts
Lw_LinesEnd:
Lw_Fold:
        movem.l d2-d7/a2-a6,-(sp)
        move.l gLwOld,a0
        move.w gLwTarget,d4
        cmp.w (a0),d4
        beq.w .done
        move.w d4,(a0)
        tst.w gLwClosing
        beq.s .opening
        neg.w d4
        addi.w #160,d4
.opening:
        move.l gLwDest,a2
        move.l gLwSource,a3
        move.l gLwRows,a4
        lea Lw_RowOffsets,a5
        lea Lw_FoldHeight,a0
        moveq #0,d3
        move.b 0(a0,d4.w),d3     ; fold height, zero at the black endpoint
        move.w d4,d6
        beq.s .fold
        subq.w #1,d6
.prefix:
        move.w (a5)+,d0
        bsr.w .row
        dbf d6,.prefix
.fold:  move.w d4,d0
        add.w d0,d0
        lea Lw_FoldFirst,a0
        move.w 0(a0,d0.w),d1
        move.w #160,d2
        sub.w d4,d2
        cmp.w d3,d2
        bhs.s .unclipped
        move.w d2,d3
.unclipped:
        sub.w d3,d2             ; remaining black rows after the fold
        move.w d3,d6
        beq.s .black
        subq.w #1,d6
.reverse:
        move.w d1,d0
        bsr.w .row
        subi.w #160,d1
        dbf d6,.reverse
.black: move.w d2,d6
        beq.s .done
        subq.w #1,d6
.blackrow:
        moveq #-1,d0
        bsr.s .row
        dbf d6,.blackrow
.done:  movem.l (sp)+,d2-d7/a2-a6
        rts
.row:
        cmpi.w #160*160,d0
        blo.s .safe             ; unsigned comparison also catches -1 below
        tst.w d0
        bmi.s .compare
        move.w #159*160,d0      ; clamp LCK's forward fold look-ahead
.safe:
.compare:
        cmp.w (a4),d0
        beq.w .skip
        move.w d0,(a4)
        move.l a2,a1
        tst.w d0
        bmi.s .clear
        lea 0(a3,d0.w),a0
        rept 40
        move.l (a0)+,(a1)+
        endr
        bra.s .skip
.clear:
        rept 40
        clr.l (a1)+
        endr
.skip:  addq.l #2,a4
        lea 160(a2),a2
        rts
Lw_FoldEnd:
Lw_Instant:
        move.l gLwOld,a0
        move.w gLwTarget,d0
        cmp.w (a0),d0
        beq.s .done
        move.w d0,(a0)
        bra.w Lw_Full
.done:  rts
Lw_InstantEnd:
Lw_PaletteSelect:
        move.w gLwTarget,d0
        tst.w gLwClosing
        beq.s .opening
        neg.w d0
        addq.w #8,d0
.opening:
        lsl.w #5,d0
        move.l gLwStages,a0
        adda.w d0,a0
        move.l a0,gLwNextPalette
        rts
Lw_PaletteSelectEnd:
Lw_Colours:
        bsr.s Lw_PaletteSelect
        move.l gLwOld,a0
        move.w (a0),d1
        move.w gLwTarget,d0
        cmp.w d1,d0
        beq.s .done
        move.w d0,(a0)
        tst.w gLwClosing
        beq.s .opening
        cmpi.w #8,d0
        beq.w Lw_Full            ; remove native pixels AFTER the palette is black
        rts
.opening:
        tst.w d1
        beq.w Lw_Full            ; each page gets its source while still black
.done:  rts
Lw_ColoursEnd:
Lw_Centre:
        move.l a4,-(sp)
        lea Lw_CentreOpen,a4
        tst.w gLwClosing
        beq.s .run
        lea Lw_CentreClose,a4
.run:   bsr.w Lw_RowList
        move.l (sp)+,a4
        rts
Lw_CentreEnd:
Lw_InterRows:
        move.l a4,-(sp)
        lea Lw_InterRowOffsets,a4
        bsr.w Lw_RowList
        move.l (sp)+,a4
        rts
Lw_InterRowsEnd:
Lw_RowList:
        movem.l d2-d7/a2-a6,-(sp)
        move.l gLwOld,a0
        move.w (a0),d0
        move.w gLwTarget,d7
        cmp.w d0,d7
        beq.w .done
        move.w d7,(a0)
        sub.w d0,d7
        subq.w #1,d7
        add.w d0,d0
        adda.w d0,a4
        move.l gLwDest,a2
        move.l gLwSource,a3
        tst.w gLwClosing
        bne.s .clear
.copy:  move.w (a4)+,d0
        lea 0(a2,d0.w),a1
        lea 0(a3,d0.w),a0
        rept 40
        move.l (a0)+,(a1)+
        endr
        dbf d7,.copy
        bra.s .done
.clear: move.w (a4)+,d0
        lea 0(a2,d0.w),a1
        rept 40
        clr.l (a1)+
        endr
        dbf d7,.clear
.done:  movem.l (sp)+,d2-d7/a2-a6
        rts
Lw_RowListEnd:
Lw_Stamp macro
        movem.l \1(a2),d0-d7/a0-a1
        move.l gLwDest,a4
        lea \1(a4),a4
        lea \1(a5),a6
.stamp\@:
        movem.l d0-d7/a0-a1,(a4)
        lea 160(a4),a4
        cmpa.l a6,a4
        blo.s .stamp\@
        endm
Lw_Smear:
        movem.l d2-d7/a2-a6,-(sp)
        move.l gLwOld,a0
        move.w (a0),d7
        move.w gLwTarget,d4
        cmp.w d7,d4
        beq.w .done
        move.w d4,(a0)
        tst.w gLwClosing
        beq.s .opening
        cmpi.w #160,d4
        bne.s .row
        bsr.w Lw_Full
        bra.w .done
.opening:
        neg.w d4
        addi.w #160,d4            ; n: upper rows all show source row n
.row:   move.w d4,d0
        add.w d0,d0
        lea Lw_RowOffsets,a0
        move.w 0(a0,d0.w),d0
        move.l gLwSource,a2
        adda.w d0,a2
        move.l gLwDest,a5
        adda.w d0,a5              ; first already-correct destination row
        tst.w gLwClosing
        bne.s .prefix
        neg.w d7
        addi.w #160,d7
        sub.w d4,d7              ; restore rows released from this page's old smear
        beq.s .prefix
        subq.w #1,d7
        move.l a2,a0
        move.l a5,a1
.tail:
        rept 40
        move.l (a0)+,(a1)+
        endr
        dbf d7,.tail
.prefix:
        tst.w d4
        beq.w .done
; Load each 40-byte source chunk once, stamp it through the upper rows.
; a2/a5 keep the source row and prefix end; pixel registers may all be used.
N       set 0
        rept 4
        Lw_Stamp N
N       set N+40
        endr
.done:  movem.l (sp)+,d2-d7/a2-a6
        rts
Lw_SmearEnd:
Lw_CurtainCols:
        move.l a4,-(sp)
        lea Lw_CurtainColumns,a4
        bsr.w Lw_Columns
        move.l (sp)+,a4
        rts
Lw_CurtainColsEnd:
Lw_InterCols:
        move.l a4,-(sp)
        lea Lw_InterColumns,a4
        bsr.w Lw_Columns
        move.l (sp)+,a4
        rts
Lw_InterColsEnd:
Lw_Columns:
        movem.l d2-d7/a2-a6,-(sp)
        move.l gLwOld,a0
        move.w (a0),d0
        move.w gLwTarget,d7
        cmp.w d0,d7
        beq.w .done
        move.w d7,(a0)
        sub.w d0,d7
        subq.w #1,d7
        lsl.w #2,d0
        adda.w d0,a4
        lea gLwColMasks,a5
        move.l a5,a0
        rept 10
        clr.l (a0)+
        endr
.merge:
        move.w (a4)+,d0          ; 8-byte planar group displacement
        lsr.w #2,d0              ; 2-byte scratch mask displacement
        move.w (a4)+,d1
        or.w d1,0(a5,d0.w)
        dbf d7,.merge
        move.l gLwDest,a2
        move.l gLwSource,a3
        moveq #19,d7
.group:
        move.w (a5)+,d2
        beq.w .next
        move.w d2,d3
        not.w d3
        move.l a2,a1
        move.l a3,a0
        move.w #159,d6
        tst.w gLwClosing
        bne.s .clear
.copy:
N       set 0
        rept 4
        move.w N(a0),d0
        and.w d2,d0
        and.w d3,N(a1)
        or.w d0,N(a1)
N       set N+2
        endr
        lea 160(a0),a0
        lea 160(a1),a1
        dbf d6,.copy
        bra.s .next
.clear:
        and.w d3,(a1)
        and.w d3,2(a1)
        and.w d3,4(a1)
        and.w d3,6(a1)
        lea 160(a1),a1
        dbf d6,.clear
.next:  addq.l #8,a2
        addq.l #8,a3
        dbf d7,.group
.done:  movem.l (sp)+,d2-d7/a2-a6
        rts
Lw_ColumnsEnd:
Lw_Full:
        movem.l d2-d7/a2-a4,-(sp)
        move.l gLwDest,a3
        lea 25600(a3),a4
        tst.w gLwClosing
        bne.s .clear
        move.l gLwSource,a2
.row:
N       set 0
        rept 5
        movem.l N(a2),d0-d7
        movem.l d0-d7,N(a3)
N       set N+32
        endr
        lea 160(a2),a2
        lea 160(a3),a3
        cmpa.l a4,a3
        blo.s .row
        bra.s .done
.clear:
        moveq #0,d0
        moveq #0,d1
        moveq #0,d2
        moveq #0,d3
        moveq #0,d4
        moveq #0,d5
        moveq #0,d6
        moveq #0,d7
.blackrow:
N       set 0
        rept 5
        movem.l d0-d7,N(a3)
N       set N+32
        endr
        lea 160(a3),a3
        cmpa.l a4,a3
        blo.s .blackrow
.done:  movem.l (sp)+,d2-d7/a2-a4
        rts
Lw_FullEnd:
Lw_Show:
        move.l gLwDest,a1
        move.l gLwSource,a0
        move.w #159,d0
.row:
        rept 40
        move.l (a0)+,(a1)+
        endr
        dbf d0,.row
        rts
Lw_ShowEnd:
        section data
        even
        xdef Lw_Picture0,Lw_Picture1,Lw_Palette0,Lw_Palette1,Lw_Limits,Lw_Speeds,Lw_Stages0,Lw_Stages1
        xdef Lw_SpiralOffsets,Lw_SnakeOffsets,Lw_RowOffsets,Lw_FoldFirst,Lw_FoldHeight
Lw_Limits: dc.w 800,160,20,320,1,8,160,160,160,320,320
Lw_Speeds: dc.w 16,2,1,4,1,1,2,2,2,2,2
Lw_Palette0: incbin "assets/PALETTE0.BIN"
Lw_Palette1: incbin "assets/PALETTE1.BIN"
Lw_Stages0: incbin "assets/STAGES0.BIN"
Lw_Stages1: incbin "assets/STAGES1.BIN"
        include "assets/tables.inc"
Lw_Picture0: incbin "assets/IMAGE0.BIN"
Lw_Picture1: incbin "assets/IMAGE1.BIN"
