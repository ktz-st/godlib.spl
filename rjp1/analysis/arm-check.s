        section code
        xdef RjpTest_Arm
        xref RjpCore_Arm
; Test-only C ABI adapter for the actual note trigger used by the sequencer.
RjpTest_Arm:
        movem.l d2-d7/a2-a6,-(sp)
        move.l a0,a3
        move.l a1,a4
        jsr RjpCore_Arm
        movem.l (sp)+,d2-d7/a2-a6
        rts
