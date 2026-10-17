; Original LINK2.EXR, TEXT-relative listing. File = TEXT + $1c.
; Extract from full-file disassembly; external parser/return labels refer to the original extension.
_L15DA:
    MOVE.L    (A7)+,(_L0000+$1B6).L       ; $15DA |
    CMP.W     #_T0005,D0                  ; $15E0 |
    BNE.W     _L02F2                      ; $15E4 |
    BSR.W     *-4890                      ; $15E8 |
    MOVE.L    D3,(_L5700).L               ; $15EC |
    BSR.W     *-4900                      ; $15F2 |
    MOVE.L    D3,(_L56FC).L               ; $15F6 |
    BSR.W     *-4910                      ; $15FC |
    MOVE.L    D3,(_L56F8).L               ; $1600 |
    BSR.W     *-4920                      ; $1606 |
    MOVE.L    D3,(_L56F4).L               ; $160A |
    BSR.W     *-4930                      ; $1610 |
    MOVE.L    D3,(_L56F0).L               ; $1614 |
    LEA       (_L56B8).L,A0               ; $161A |
    MOVEM.L   D5-D6/A1-A6,-(A0)           ; $1620 |
    MOVEA.L   (_L56F0).L,A0               ; $1624 |
    MOVE.L    (_L56F4).L,D0               ; $162A |
    MOVE.L    (_L56F8).L,D1               ; $1630 |
    MOVEA.L   (_L56FC).L,A1               ; $1636 |
    MOVE.L    (_L5700).L,D2               ; $163C |
    TST.W     D0                          ; $1642 |
    BGE.S     _L1648                      ; $1644 |
    MOVEQ     #0,D0                       ; $1646 |
_L1648:
    TST.W     D1                          ; $1648 |
    BGE.S     _L164E                      ; $164A |
    MOVEQ     #0,D1                       ; $164C |
_L164E:
    TST.W     D2                          ; $164E |
    BGE.S     _L1654                      ; $1650 |
    MOVEQ     #0,D2                       ; $1652 |
_L1654:
    CMPI.W    #$C7,D0                     ; $1654 |
    BLE.S     _L165E                      ; $1658 |
    MOVE.W    #$C7,D0                     ; $165A |
_L165E:
    CMPI.W    #$C7,D1                     ; $165E |
    BLE.S     _L1668                      ; $1662 |
    MOVE.W    #$C7,D1                     ; $1664 |
_L1668:
    CMPI.W    #$C7,D2                     ; $1668 |
    BLE.S     _L1672                      ; $166C |
    MOVE.W    #$C7,D2                     ; $166E |
_L1672:
    MOVEQ     #0,D7                       ; $1672 |
    MOVE.W    D1,D7                       ; $1674 |
    SUB.W     D0,D7                       ; $1676 |
    SUBQ.W    #1,D7                       ; $1678 |
    ADD.W     D7,D0                       ; $167A |
    ADD.W     D0,D0                       ; $167C |
    LEA       _L4180(PC),A2               ; $167E |
    ADDA.W    D0,A2                       ; $1682 |
    ADDA.W    (A2),A0                     ; $1684 |
    MOVE.W    #$C7,D6                     ; $1686 |
    SUB.W     D2,D6                       ; $168A |
    TST.W     D6                          ; $168C |
    BLE.S     _L16FC                      ; $168E |
    SUBQ.W    #7,D7                       ; $1690 |
    LSR.W     #1,D7                       ; $1692 |
    CMP.W     D6,D7                       ; $1694 |
    BLE.S     _L169A                      ; $1696 |
    MOVE.W    D6,D7                       ; $1698 |
_L169A:
    ADD.W     D2,D2                       ; $169A |
    LEA       _L4180(PC),A2               ; $169C |
    ADDA.W    D2,A2                       ; $16A0 |
    ADDA.W    (A2),A1                     ; $16A2 |
    LEA       _L170E(PC),A2               ; $16A4 |
    MOVEM.W   (A2),D0-D1                  ; $16A8 |
    TST.W     D0                          ; $16AC |
    BEQ.S     _L16B2                      ; $16AE |
    ADDQ.W    #2,D1                       ; $16B0 |
_L16B2:
    EORI.W    #1,D0                       ; $16B2 |
    CMPI.W    #38,D1                      ; $16B6 |
    BLE.S     _L16BE                      ; $16BA |
    MOVEQ     #0,D1                       ; $16BC |
_L16BE:
    MOVEM.W   D0-D1,(A2)                  ; $16BE |
    LEA       *+80(PC,D1.W),A2            ; $16C2 |
_L16C6:
    MOVEM.L   (A0),D0-D6/A3-A6            ; $16C6 |
    MOVEM.L   D0-D6/A3-A6,(A1)            ; $16CA |
    MOVEM.L   $2C(A0),D0-D6/A3-A6         ; $16CE |
    MOVEM.L   D0-D6/A3-A6,$2C(A1)         ; $16D4 |
    MOVEM.L   $58(A0),D0-D6/A3-A6         ; $16DA |
    MOVEM.L   D0-D6/A3-A6,$58(A1)         ; $16E0 |
    MOVEM.L   $84(A0),D0-D6               ; $16E6 |
    MOVEM.L   D0-D6,$84(A1)               ; $16EC |
    SUBA.W    (A2)+,A0                    ; $16F2 |
    LEA       $A0(A1),A1                  ; $16F4 |
    DBRA      D7,_L16C6                   ; $16F8 |
_L16FC:
    LEA       (_L5698).L,A0               ; $16FC |
    MOVEM.L   (A0)+,D5-D6/A1-A6           ; $1702 |
    MOVEA.L   (_L0000+$1B6).L,A0          ; $1706 |
    JMP       (A0)                        ; $170C |

; $170e: dc.w 0,0 ; toggle, phase bytes
; $1712: rept 80
; dc.w 160,160,320,320,320,480,480,640,640,480,480,320,320,160,320,320,160,160,160,0
; endr
; $4180: 200 words y*160
