        section .text,code
        xdef TfmxRef_Init,TfmxRef_Start,TfmxRef_Tick
TfmxRef_Init:
        movem.l d3-d7/a2-a6,-(sp)
        move.l a0,d0
        move.l a1,d1
        bsr _tfmxInit_asm
        movem.l (sp)+,d3-d7/a2-a6
        rts
TfmxRef_Start:
        movem.l d3-d7/a2-a6,-(sp)
        bsr _tfmxStartSong_asm
        movem.l (sp)+,d3-d7/a2-a6
        rts
TfmxRef_Tick:
        movem.l d3-d7/a2-a6,-(sp)
        bsr _tfmxTick_asm
        movem.l (sp)+,d3-d7/a2-a6
        rts
        include "analysis/reference-core.s"
