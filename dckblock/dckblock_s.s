; DCK planar block-copy adaptation, 68000, four interleaved ST planes.
; A command is seven words: src offset, dst offset, width (16px groups),
; height, plane mask, signed source-row step, signed destination-row step.
; Immutable 320x160 source; destination is the logical stage at Y24.
        section text
        xdef Db_Init,Db_Frame,Db_FrameEnd,Db_Prepare,Db_PrepareEnd
        xdef Db_Execute,Db_ExecuteEnd,Db_Copy,Db_CopyEnd,Db_Show,Db_ShowEnd
        xdef Db_RowsStart,Db_RowsEnd,Db_Picture,Db_Palette,Db_Positions
        xref gDbDest,gDbMode,gDbMask,gDbPhase,gDbPaused,gDbPage
        xref gDbHistory,gDbCommands,gDbCount
Db_Init:
        clr.w gDbPhase
        move.l #$ffff0000,gDbHistory
        move.l #$ffff0000,gDbHistory+8
        clr.l gDbHistory+4
        clr.l gDbHistory+12
        rts
Db_Frame:
        movem.l d0-d7/a0-a6,-(sp)
        tst.w gDbPaused
        bne.s .prepare
        addq.w #1,gDbPhase
        cmpi.w #160,gDbPhase
        blo.s .prepare
        clr.w gDbPhase
.prepare:
        bsr Db_Prepare
        bsr Db_Execute
        movem.l (sp)+,d0-d7/a0-a6
        rts
Db_FrameEnd:
Db_Prepare:
        clr.w gDbCount
        move.w gDbPage,d0
        lsl.w #3,d0
        lea gDbHistory,a4
        adda.w d0,a4
        move.w gDbPhase,d0
        cmpi.w #4,gDbMode
        bne.s .key
        lsr.w #4,d0              ; strips change only once per 16 ticks
.key:   move.w gDbMode,d1
        cmp.w (a4),d1
        bne.s .changed
        move.w gDbMask,d1
        cmp.w 2(a4),d1
        bne.s .changed
        cmp.w 4(a4),d0
        beq .done               ; both buffers settle independently on pause
.changed:
        move.w d0,4(a4)
        lea gDbCommands,a5
        move.w 2(a4),d4
        beq.s .new
        moveq #0,d0
        moveq #20,d2
        move.w #160,d3
        tst.w (a4)
        bne.s .notmove
        move.w 6(a4),d0         ; old moving rectangle
        moveq #8,d2
        moveq #64,d3
        bra.s .footprint
.notmove:
        cmpi.w #4,(a4)
        bne.s .footprint
        move.w #40*160,d0      ; old strips affect only the middle 80 rows
        moveq #80,d3
.footprint:
        tst.w gDbMode
        beq.s .restore          ; new moving block cannot cover old footprint
        cmpi.w #4,gDbMode
        bne.s .inactive         ; new full-stage effect covers active planes
        cmpi.w #4,(a4)
        bne.s .restore          ; entering the smaller strip window
.inactive:
        move.w gDbMask,d1
        not.w d1
        and.w d1,d4
.restore:
        move.w d0,d1
        move.w #160,d5
        move.w d5,d6
        bsr Db_Append
.new:   move.w gDbMode,(a4)
        move.w gDbMask,2(a4)
        move.w gDbMode,d0
        lsl.w #2,d0
        lea Db_Builders,a0
        move.l 0(a0,d0.w),a0
        jsr (a0)
.done:  rts
Db_Append:
        tst.w d3
        beq.s .done
        tst.w d4
        beq.s .done
        move.w d0,(a5)+
        move.w d1,(a5)+
        move.w d2,(a5)+
        move.w d3,(a5)+
        move.w d4,(a5)+
        move.w d5,(a5)+
        move.w d6,(a5)+
        addq.w #1,gDbCount
.done:  rts
Db_Move:
        move.w gDbPhase,d0
        add.w d0,d0
        lea Db_Positions,a0
        move.w 0(a0,d0.w),d1
        move.w d1,6(a4)
        move.w #24*160+48,d0   ; source X96,Y24, 128x64
        moveq #8,d2
        moveq #64,d3
        move.w gDbMask,d4
        move.w #160,d5
        move.w d5,d6
        bra Db_Append
Db_Repeat:
        move.w gDbPhase,d0
        mulu.w #160,d0
        moveq #0,d1
        moveq #20,d2
        moveq #16,d3
        move.w gDbMask,d4
        moveq #0,d5            ; repeat a source row sixteen times
        move.w #160,d6
        moveq #9,d7
.band:  bsr Db_Append
        addi.w #2560,d0
        cmpi.w #25600,d0
        blo.s .nowrap
        subi.w #25600,d0
.nowrap:
        addi.w #2560,d1
        dbf d7,.band
        rts
Db_Skip:
        move.w gDbPhase,d0
        cmpi.w #80,d0
        blo.s .forward
        neg.w d0
        addi.w #159,d0
.forward:
        mulu.w #160,d0
        movea.w d0,a0
        moveq #0,d1
        moveq #20,d2
        moveq #40,d3
        move.w gDbMask,d4
        move.w #320,d5         ; sample every second source row
        move.w #160,d6
        bsr Db_Append
        move.w a0,d0
        neg.w d0
        addi.w #79*160,d0
        move.w #40*160,d1
        bsr Db_Append
        move.w a0,d0
        neg.w d0
        addi.w #159*160,d0
        move.w #80*160,d1
        move.w #-320,d5        ; independent backwards source stride
        bsr Db_Append
        move.w a0,d0
        addi.w #80*160,d0
        move.w #120*160,d1
        bra Db_Append
Db_Flip:
        moveq #0,d0
        move.w #159,d1
        sub.w gDbPhase,d1
        mulu.w #160,d1
        moveq #20,d2
        move.w #160,d3
        sub.w gDbPhase,d3
        move.w gDbMask,d4
        move.w #160,d5
        move.w #-160,d6        ; source forwards, destination backwards
        bsr Db_Append
        move.w #160,d0
        sub.w gDbPhase,d0
        mulu.w #160,d0
        move.w #159*160,d1
        move.w gDbPhase,d3
        bra Db_Append           ; zero-height second command is ignored
Db_Strips:
        move.w gDbPhase,d0
        andi.w #$fff0,d0        ; (phase/16) * 16-byte (32px) strip offset
        addi.w #40*160,d0
        move.w #40*160,d1
        moveq #2,d2
        moveq #80,d3
        move.w gDbMask,d4
        move.w #160,d5
        move.w d5,d6
        moveq #9,d7
.strip: btst #0,d7
        bne.s .forward
        addi.w #79*160,d0
        neg.w d5
.forward:
        bsr Db_Append
        tst.w d5
        bpl.s .next
        subi.w #79*160,d0
        neg.w d5
.next:  addi.w #16,d0
        cmpi.w #41*160,d0
        blo.s .nowrap
        subi.w #160,d0
.nowrap:
        addi.w #16,d1
        dbf d7,.strip
        rts
Db_PrepareEnd:
Db_Execute:
        move.w gDbCount,d7
        beq.s .done
        subq.w #1,d7
        lea gDbCommands,a2
.command:
        movem.l d7/a2,-(sp)
        bsr Db_Copy
        movem.l (sp)+,d7/a2
        lea 14(a2),a2
        dbf d7,.command
.done:  rts
Db_ExecuteEnd:
; Internal register ABI: a2 points to a validated command. All registers may
; be clobbered. Source/destination pointers remain constant inside a row kernel.
; Widths 2/8/20, masks 0..15; height 0 and mask 0 perform no memory access.
Db_Copy:
        move.w 6(a2),d1
        beq .done
        move.w 8(a2),d0
        andi.w #15,d0
        beq .done
        lsl.w #2,d0
        move.w 4(a2),d2
        cmpi.w #2,d2
        beq.s .width
        addi.w #64,d0
        cmpi.w #8,d2
        beq.s .width
        cmpi.w #20,d2
        bne .done
        addi.w #64,d0
.width: lea Db_RowTable,a0
        move.l 0(a0,d0.w),a6
        lea Db_Picture,a0
        adda.w (a2),a0
        move.l gDbDest,a1
        adda.w 2(a2),a1
        cmpi.w #15,8(a2)
        bne.s .registers
        cmpi.w #2,d2
        beq.s .registers
        ; Wide MOVEM rows use all free registers. Keep three words on stack;
        ; the row kernel loops internally, with just one call per rectangle.
        subq.w #1,d1
        move.w d1,-(sp)
        move.w 12(a2),-(sp)
        move.w 10(a2),-(sp)
        jsr (a6)
        lea 6(sp),sp
        rts
.registers:
        ; Partial masks and 32px rows leave d4-d6 available for a DBF loop.
        move.w 10(a2),d4
        move.w 12(a2),d5
        move.w d1,d6
        subq.w #1,d6
        jsr (a6)
.done:  rts
Db_CopyEnd:
Db_Show:
        movem.l d0-d7/a0-a6,-(sp)
        lea Db_Clean,a2
        bsr Db_Copy
        movem.l (sp)+,d0-d7/a0-a6
        rts
Db_ShowEnd:
        include "assets/rows.inc"
        section data
Db_Builders: dc.l Db_Move,Db_Repeat,Db_Skip,Db_Flip,Db_Strips
Db_Clean: dc.w 0,0,20,160,15,160,160
Db_Palette: incbin "assets/PALETTE.BIN"
Db_Picture: incbin "assets/PICTURE.BIN"
Db_Positions: incbin "assets/MOVE.BIN"
        even
