        section data
        even
        xdef Cut_Castle,Cut_Forest,Cut_FontSheet,Cut_StarData,Cut_Script,Cut_ScriptEnd
Cut_Castle: incbin 'assets/CASTLE.PI1'
        even
Cut_Forest: incbin 'assets/FOREST.PI1'
        even
Cut_FontSheet: incbin 'assets/FONT.BIN'
Cut_StarData: incbin 'assets/STAR.BIN'
        xdef Cut_Voice0,Cut_Voice0End
Cut_Voice0: incbin 'assets/ARRIVAL.RAW'
Cut_Voice0End:
        even
        xdef Cut_Voice1,Cut_Voice1End
Cut_Voice1: incbin 'assets/PATH.RAW'
Cut_Voice1End:
        even
        xdef Cut_Voice2,Cut_Voice2End
Cut_Voice2: incbin 'assets/FOREST.RAW'
Cut_Voice2End:
        even
        xdef Cut_Voice3,Cut_Voice3End
Cut_Voice3: incbin 'assets/JOURNEY.RAW'
Cut_Voice3End:
        even
Cut_Script: incbin 'scene.txt'
Cut_ScriptEnd:
        dc.b 0
        even
