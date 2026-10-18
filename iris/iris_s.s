; Embedded clean artwork, palettes and original Q14 sine values.
        section data
        even
        xdef Iris_Image,Iris_Image2,Iris_Palette,Iris_Palette2,Iris_Sine
Iris_Image: incbin 'assets/IMAGE.BIN'
Iris_Image2: incbin 'assets/IMAGE2.BIN'
Iris_Palette: incbin 'assets/PALETTE.BIN'
Iris_Palette2: incbin 'assets/PALETTE2.BIN'
Iris_Sine:
        include 'assets/SINE.S'
