        section data
        even
        xdef Fe_Menu,Fe_MenuEnd
Fe_Menu: incbin "assets/MENU.FED"
Fe_MenuEnd:
        even
        xdef Fe_Normal,Fe_NormalEnd
Fe_Normal: incbin "assets/NORMAL.BFB"
Fe_NormalEnd:
        even
        xdef Fe_Active,Fe_ActiveEnd
Fe_Active: incbin "assets/ACTIVE.BFB"
Fe_ActiveEnd:
        even
        xdef Fe_Title,Fe_TitleEnd
Fe_Title: incbin "assets/TITLE.BFB"
Fe_TitleEnd:
        even
        xdef Fe_Cursor,Fe_CursorEnd
Fe_Cursor: incbin "assets/CURSOR.BSB"
Fe_CursorEnd:
        even
        xdef Fe_Main,Fe_MainEnd
Fe_Main: incbin "assets/MAIN.PI1"
Fe_MainEnd:
        even
        xdef Fe_Options,Fe_OptionsEnd
Fe_Options: incbin "assets/OPTIONS.PI1"
Fe_OptionsEnd:
        even
        xdef Fe_Chime,Fe_ChimeEnd
Fe_Chime: incbin "assets/CHIME.RAW"
Fe_ChimeEnd:
