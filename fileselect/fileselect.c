/* GEM owns the display/IKBD here: deliberately do not call Platform_Init. */
#include <godlib/file/file.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/memory/memory.h>
#include <godlib/string/string.h>
#include <stdio.h>

sFileIdentifier gSelector;
volatile U16 gSelectorReady, gSelectorResult, gSelectorCalls;
volatile S32 gSelectedSize = -1;
char gSelectedPath[512];
char gPreview[161];

static void Print(const char *text) { GemDos_Cconws(text); }

/* TOS's console does not wrap long lines automatically. */
static void PrintWrapped(const char *text)
{
    char row[38];
    U16 count;
    while (*text)
    {
        count = 0;
        while (*text && count < 36) row[count++] = *text++;
        row[count] = 0;
        Print(" "); Print(row); Print("\r\n");
    }
}

static void Select(void)
{
    char *full;
    char line[80];
    sFileHandle handle;
    S32 count;
    U16 i;
    Print("\033E GodLib File_Selector / GEM AES\r\n\r\n");
    gSelectorReady = 0;
    gSelectorResult = File_Selector("Choose a file", &gSelector);
    ++gSelectorCalls;
    gSelectedSize = -1;
    gSelectedPath[0] = gPreview[0] = 0;
    Print("\033E GodLib File_Selector / GEM AES\r\n\r\n");
    if (gSelectorResult && gSelector.mpStrings[eFILEIDENTIFIER_FILENAME][0])
    {
        full = File_Identifier_ToFullName(&gSelector);
        if (full)
        {
            String_StrCpy(gSelectedPath, full);
            Print(" Selected:\r\n"); PrintWrapped(full);
            gSelectedSize = File_GetSize(full);
            if (gSelectedSize >= 0)
                sprintf(line, " Size: %ld bytes\r\n\r\n", (long)gSelectedSize);
            else
                sprintf(line, " File error: %ld\r\n\r\n", (long)gSelectedSize);
            Print(line);
            handle = File_Open(full);
            if (File_HandleIsValid(handle))
            {
                count = File_Read(handle, 160, gPreview);
                File_Close(handle);
                if (count < 0) count = 0;
                for (i = 0; i < (U16)count; ++i)
                    if ((U8)gPreview[i] < 32 || (U8)gPreview[i] > 126)
                        gPreview[i] = '.';
                gPreview[count] = 0;
                Print(" First 160 bytes (read only):\r\n");
                PrintWrapped(gPreview);
            }
            else Print(" Cannot open this file.\r\n");
            mMEMFREE(full);
        }
    }
    else Print(" Cancelled. No file was opened.\r\n");
    Print("\r\n O/Space: open again   T: *.TXT\r\n A: *.*   Q/Esc: exit\r\n\r\n");
    Print(" Use the mouse inside the GEM dialog.\r\n");
    gSelectorReady = 1;
}

S16 GodLib_Game_Main(S16 argc, char **argv)
{
    U16 key;
    (void)argc; (void)argv;
    Memory_Init();
    File_Identifier_Init(&gSelector);
    File_Identifier_SetFileName(&gSelector, "");
    File_Identifier_SetMask(&gSelector, "*.TXT");
    Select();
    for (;;)
    {
        key = (U16)GemDos_Cconin() & 255;
        if (key == 27 || key == 'q' || key == 'Q') break;
        if (key == 't' || key == 'T') File_Identifier_SetMask(&gSelector, "*.TXT");
        else if (key == 'a' || key == 'A') File_Identifier_SetMask(&gSelector, "*.*");
        else if (key != 'o' && key != 'O' && key != ' ') continue;
        Select();
    }
    File_Identifier_DeInit(&gSelector);
    Memory_DeInit();
    return 0;
}
