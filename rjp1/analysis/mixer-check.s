        section code
        xdef RjpMixerTest_Arm
        xref RjpCore_Arm
; C ABI: a0 shadow voice, a1 data, d0 attack words, d1 loop words,d2 offset.
RjpMixerTest_Arm:
        movem.l d2-d7/a2-a6,-(sp)
        move.l a0,a3
        move.l a1,a4
        lea .globals,a5
        moveq #0,d3
        jsr RjpCore_Arm
        movem.l (sp)+,d2-d7/a2-a6
        rts
        section .bss,bss
.globals: ds.b 48
