        section text
        xdef WipeBench_Update
        xref Wipe_Update,gWipeBenchAbiFailed
WipeBench_Update:
        movem.l d2-d7/a2-a6,-(sp)
        movem.l .patterns(pc),d2-d7/a2-a6
        jsr Wipe_Update
        movem.l d2-d7/a2-a6,WipeBench_Actual
        lea WipeBench_Actual,a0
        lea .patterns(pc),a1
        moveq #10,d0
.check: move.l (a0)+,d1
        cmp.l (a1)+,d1
        beq.s .next
        move.w #1,gWipeBenchAbiFailed
.next:  dbf d0,.check
        movem.l (sp)+,d2-d7/a2-a6
        rts
.patterns: dc.l $24680000,$24680101,$24680202,$24680303,$24680404,$24680505,$24680606,$24680707,$24680808,$24680909,$24680a0a
        section bss
WipeBench_Actual: ds.l 11
