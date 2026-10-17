        section text
        xdef Moon_Render,Moon_RenderEnd,Moon_Clear,Moon_ClearEnd,Moon_Draw,Moon_DrawEnd
        xref gMoonScreen,gMoonBackground,gMoonSprite,gMoonForeground
        xref gMoonWorkGfx,gMoonWorkMask
        xref gMoonDirty,gMoonRows,gMoonWords
        xref gMoonColourSkip,gMoonMaskSkip,gMoonSpriteSkip
; Fixed ST-low canvas. Sprite phases contain mask + 4 plane words per group.
Moon_Render:
        movem.l d2-d7/a2-a6,-(sp)
        bsr Moon_Clear
        bsr Moon_Draw
        movem.l (sp)+,d2-d7/a2-a6
        rts
Moon_RenderEnd:
Moon_Clear:
        move.l gMoonDirty,a5
        move.w 4(a5),d7
        beq.w .done
        subq.w #1,d7
        move.l (a5),d0
        move.l gMoonBackground,a1
        adda.l d0,a1
        move.l gMoonScreen,a0
        adda.l d0,a0
        move.w 6(a5),d3
        move.w d3,d4
        lsl.w #3,d4
        neg.w d4
        add.w #160,d4
        subq.w #1,d3
.row:
        move.w d3,d6
.group:
        move.l (a1)+,(a0)+
        move.l (a1)+,(a0)+
        dbf d6,.group
        adda.w d4,a1
        adda.w d4,a0
        dbf d7,.row
.done:
        rts
Moon_ClearEnd:
Moon_Draw:
        move.w gMoonRows,d7
        beq.w .done
        subq.w #1,d7
        lea gMoonWorkGfx,a0
        lea gMoonWorkMask,a3
        move.l gMoonForeground,a1
        move.l gMoonSprite,a2
        move.w gMoonColourSkip,d3
        sub.w #128,d3         ; work gfx stride 32, not screen stride 160
        move.w gMoonMaskSkip,d4
        sub.w #32,d4          ; work mask stride 8, not scene stride 40
        move.w gMoonSpriteSkip,d5
.row:
        move.w gMoonWords,d6
        subq.w #1,d6
.group:
        move.w (a2)+,d0       ; sprite shape: 1 = solid moon
        move.w (a1)+,d1       ; scene mask: 1 = foreground
        not.w d1
        and.w d1,d0           ; visible = shape & ~foreground
        move.w d0,d1
        not.w d1
        move.w d1,(a3)+       ; GodLib preserve mask: 1 = keep background
        rept 4
        move.w (a2)+,d2
        and.w d0,d2
        move.w d2,(a0)+       ; hidden colour bits must also be zero for OR
        endr
        dbf d6,.group
        adda.w d3,a0
        adda.w gMoonMaskSkip,a1
        adda.w d4,a3
        adda.w d5,a2
        dbf d7,.row
.done:
        rts
Moon_DrawEnd:
        section data
        even
        xdef Moon_Image,Moon_Palette,Moon_Foreground,Moon_Phases,Moon_Path
Moon_Image: incbin 'assets/IMAGE.BIN'
Moon_Palette: incbin 'assets/PALETTE.BIN'
Moon_Foreground: incbin 'assets/FORE.BIN'
Moon_Phases: incbin 'assets/PHASES.BIN'
Moon_Path: incbin 'assets/PATH.BIN'

        xdef Star_Frames,Star_Positions
Star_Frames: incbin 'assets/STARS.BIN'
Star_Positions: incbin 'assets/STARPOS.BIN'
