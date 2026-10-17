; THE NIBBLE SCROLL: Manikin / The Lost Boys, concept by XXX, 19-Apr-1989.
; GodLib/vasm adaptation. Original 15-row ROXL conveyor, two-pixel advance,
; 8-pixel sine strips, waveform data and font. No BLiTTER or raster IRQ needed.
        section text
        xdef Nibble_Advance,Nibble_AdvanceEnd,Nibble_Shift,Nibble_ShiftEnd
        xdef Nibble_Draw,Nibble_DrawEnd,Nibble_Clear,Nibble_ClearEnd
        xdef Nibble_DrawFlat,Nibble_DrawFlatEnd
        xref gNibbleScreen,gNibbleWaveData,gNibbleText,gNibbleCount
        xref gNibbleGlyph,gNibbleBuffer,gNibblePhase
Nibble_Advance:
        movem.l d0-d7/a0-a6,-(sp)
        subq.w #1,gNibbleCount
        bne.s Nibble_Shift
        move.w #16,gNibbleCount
        move.l gNibbleText,a0
.next:
        moveq #0,d0
        move.b (a0)+,d0
        bne.s .letter
        lea Nibble_Text,a0
        bra.s .next
.letter:
        move.l a0,gNibbleText
        sub.w #32,d0
        lsl.w #6,d0
        lea Nibble_Font,a0
        adda.w d0,a0
        lea gNibbleGlyph,a1
        movem.l (a0)+,d0-d7
        movem.l d0-d7,(a1)
        movem.l (a0)+,d0-d7
        movem.l d0-d7,32(a1)
Nibble_Shift:
        moveq #14,d0            ; actual original height is 15, not 16
        lea gNibbleGlyph,a1
        lea gNibbleBuffer,a0
.row:
        rept 2
        lsl.w 2(a1)
        roxl.w (a1)
N       set 570
        rept 20
        roxl.w N(a0)
N       set N-30
        endr
        endr
        lea 4(a1),a1
        addq.l #2,a0
        dbf d0,.row
Nibble_ShiftEnd:
        addq.w #1,gNibblePhase
        cmp.w #80,gNibblePhase
        bne.s .done
        clr.w gNibblePhase
.done:
        movem.l (sp)+,d0-d7/a0-a6
        rts
Nibble_AdvanceEnd:
Nibble_Draw:
        movem.l d0-d7/a0-a6,-(sp)
        move.l gNibbleWaveData,a0
        move.w gNibblePhase,d0
        lsl.w #2,d0
        adda.w d0,a0
        lea gNibbleBuffer,a1
        move.l gNibbleScreen,a4
        lea 80*160(a4),a4
        moveq #19,d7
.column:
        move.l a4,a2
        move.l a2,a3
        addq.l #8,a4
        move.l (a0)+,d4
        adda.w d4,a3
        swap d4
        adda.w d4,a2
        ; Same margins as the original: each page advances two frames between
        ; redraws, and the two 8px halves may have different Y positions.
        moveq #0,d5
        move.w d5,-800(a2)
        move.w d5,-640(a2)
        move.w d5,-480(a2)
        move.w d5,-320(a2)
        move.w d5,-160(a2)
        move.w d5,(a2)
        move.w d5,(a3)
        move.w d5,160(a3)
        move.w d5,2560(a3)
        move.w d5,2400(a3)
        move.w d5,2560(a2)
        move.w d5,2720(a2)
        move.w d5,2880(a2)
        move.w d5,3040(a2)
        move.w d5,3200(a2)
        move.w d5,3360(a2)
Y       set 160
        rept 15
        move.b (a1)+,Y(a2)
        move.b (a1)+,Y+1(a3)
Y       set Y+160
        endr
        dbf d7,.column
        movem.l (sp)+,d0-d7/a0-a6
        rts
Nibble_DrawEnd:
; Straight scroller: same conveyor/font/speed, one word per 16px column.
; No sine lookups or steady-state erasing: all 15 rows are overwritten.
Nibble_DrawFlat:
        movem.l d0/a0-a1,-(sp)
        lea gNibbleBuffer,a0
        move.l gNibbleScreen,a1
        lea 101*160(a1),a1
        moveq #19,d0
.column:
Y       set 0
        rept 15
        move.w (a0)+,Y(a1)
Y       set Y+160
        endr
        addq.l #8,a1
        dbf d0,.column
        movem.l (sp)+,d0/a0-a1
        rts
Nibble_DrawFlatEnd:
; Rare full-band clear on a waveform change. Only plane zero is modified.
Nibble_Clear:
        movem.l d0-d1/a0,-(sp)
        move.l gNibbleScreen,a0
        lea 75*160(a0),a0
        moveq #0,d0
        moveq #66,d1
.row:
X       set 0
        rept 20
        move.w d0,X(a0)
X       set X+8
        endr
        lea 160(a0),a0
        dbf d1,.row
        movem.l (sp)+,d0-d1/a0
        rts
Nibble_ClearEnd:
        section data
        even
        xdef Nibble_Waves,Nibble_Font,Nibble_Text
Nibble_Waves:
        incbin 'assets/NIBBLE.DAT'
        incbin 'assets/NIBBLE1.DAT'
Nibble_Font:
        incbin 'assets/LOST16.FON'
Nibble_Text:
        dc.b 'SIEMKA!  GODLIB PRESENTS THE NIBBLE SCROLL!    '
        dc.b 'CODING BY MANIKIN.  CONCEPT BY XXX.  THE LOST BOYS 1989.    '
        dc.b 'A LOVELY SINE CURVE... AND ONLY ONE BITPLANE!    '
        dc.b 'NO BLITTER NEEDED.  GREETINGS TO ALL ST AND STE CODERS!    ',0
        even
