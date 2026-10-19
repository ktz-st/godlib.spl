/* Native GodLib widgets and GuiFS, constructed with writable C data. */
#include <godlib/gui/gui.h>
#include <godlib/gui/guidata.h>
#include <godlib/gui/guifs.h>
#include <godlib/gui/guiedit.h>
#include <godlib/gui/r_gui.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/font/font.h>
#include <godlib/sprite/sprite.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/video/video.h>
#include <godlib/fade/fade.h>
#include <godlib/memory/memory.h>
#include <godlib/string/string.h>
#include <stdio.h>
extern U16 Gui_FontSheet[],Gui_CursorData[];
static sHashTree tree;
static sGuiData data;
static sGuiWindow windows[4];
static sGuiButton buttons[40];
static U16 buttonCount;
static sGuiInfo *rootControls[4],*demoControls[16],*fsControls[16];
static sGuiSlider sliders[2];
static sGuiColour colours[16];
static sGuiFill fills[7];
static sGuiButtonStyle styles[5];
static sGuiFontGroup fontGroup;
static sGuiAsset fontAsset,cursorAsset;
static sGuiCursor cursor;
static sFont *font;
static sSprite cursorSprite;
static sSpriteBlock cursorBlock;
static sGuiVar vars[5];
static sHashTreeVar values[7];
static sHashTreeVarClient clients[4];
static sGuiValue gainValue;
static sGuiAction exitAction,closeAction;
static sGuiFSInfo selector;
static sString statusText;
sString gGuiName;
volatile S32 gGuiGain;
volatile U16 gGuiReady,gGuiExited,gGuiOpenCount,gGuiCallbacks,gGuiApplyCount,gGuiListCount;
volatile S16 gGuiScrollY;
volatile S16 gGuiMouseX,gGuiMouseY;
volatile U32 gGuiCleanupVars;
const U16 gGuiButtonSize=sizeof(sGuiButton),gGuiWindowSize=sizeof(sGuiWindow);
const U16 gGuiNameOffset=mOFFSET(sGuiButton,mInfo.mpName),gGuiTitleOffset=mOFFSET(sGuiButton,mString.mpTitle);
volatile U32 gGuiFrame,gGuiTreeCount;
char gGuiSelected[256];
static U16 palette[16]={0x001,0xfff,0x123,0x235,0x5cf,0x067,0xf90,0xf33,0,0,0,0,0,0,0,0xfff};
static void rect(sGuiInfo *i,U16 type,char *name,S16 x,S16 y,S16 w,S16 h)
{i->mType=type;i->mpName=name;i->mRectPair.mLocal=(sGuiRect){x,y,w,h};i->mRedrawFlag=2;}
static sGuiButton *button(char *name,char *text,S16 x,S16 y,S16 w,S16 h,U16 style,U16 type)
{
 sGuiButton *b=&buttons[buttonCount++];rect(&b->mInfo,eGUI_TYPE_BUTTON,name,x,y,w,h);
 b->mButtonType=type;b->mpStyle=&styles[style];b->mString.mpTitle=text;
 b->mString.mAlign.mV=eGUI_ALIGNV_CENTRE;
 if(type==eGUI_BUTTON_SPRING)b->mString.mAlign.mH=eGUI_ALIGNH_CENTRE;
 /* StringDraw adds 2 px itself; inset the field by another 2 for 4 px padding. */
 if(style==2){b->mString.mAlign.mH=eGUI_ALIGNH_LEFT;b->mString.mRects.mLocal.mX=2;b->mString.mRects.mLocal.mWidth=-2;}
 return b;
}
static void bindString(sGuiButton *b,char *name)
{b->mString.mVar.mpName=name;b->mString.mVar.mType=eGUI_VAR_STRING;}
static void var(U16 i,char *name,S32 value)
{vars[i].mpName=name;vars[i].mType=eGUI_VAR_S32;HashTree_Var_Init(&values[i],&tree,name,4,&value);HashTree_VarWrite(&values[i],&value);HashTree_VarClient_Init(&vars[i].mVarClient,&tree,name,0);}
static U32 countVars(void)
{U32 n=0;sHashTreeVar *v;for(v=tree.mpVars;v;v=v->mpVarNext)++n;return n;}
static void status(const char *text)
{sString *p=&statusText;String_Set(p,text);HashTree_VarWrite(&values[6],&p);}
static void selected(sGuiFSInfo *info)
{
 ++gGuiCallbacks;
 if(info->mButton==eGUIFS_BUTTON_OK){
  sString *path=GuiFSInfo_FullNameBuild(info);
  snprintf(gGuiSelected,sizeof(gGuiSelected),"%s",path?path->mpChars:"");
  status(info->mFileName.mpChars);
  if(path){String_DeInit(path);_Memory_Release(path);}
 }else status("SELECTION CANCELLED");
}
static void clicked(sHashTreeVarClient *client)
{
 sGuiEvent *e=(sGuiEvent*)client->mpVar->mpData;
 if(e->mEvent!=eGUIEVENT_BUTTON_LEFTCLICK)return;
 switch(client->mUserData){
 case 0:{char message[48];++gGuiApplyCount;snprintf(message,sizeof(message),"HELLO %s!",gGuiName.mpChars);status(message);break;}
 case 1:{S32 value=50;sString *p=&gGuiName;String_Set(p,"ATARI");HashTree_VarWrite(&values[5],&p);HashTree_VarWrite(&values[0],&value);Gui_WorldPosUpdate();status("SETTINGS RESET");break;}
 case 2:++gGuiOpenCount;GuiFS_Open(&selector);break;
 }
}
static sFont *makeFont(void)
{
 sSpriteBlock *block=Sprite_BlockCreate(127);sFont *result=0;U8 map[128];U16 i;
 if(!block)return 0;
 for(i=0;i<127;++i){U16 c=i+1;U32 offset=(U32)(c/20)*6*80+(c%20)*4;
  U16 *mask=Sprite_MaskCreate(Gui_FontSheet+offset,16,6,4,4,0);
  block->mpSprite[i]=Sprite_Create(Gui_FontSheet+offset,mask,16,6,4,4,0);Sprite_MaskDestroy(mask);map[i]=(U8)c;
  if(!block->mpSprite[i]){Sprite_BlockDestroy(block);return 0;}
 }
 map[127]=0;result=Font_Create(block,map,6);Sprite_BlockDestroy(block);
 if(result){result->mSpaceWidth=6;result->mKerning=0;result->mWidthMax=6;result->mHeightMax=6;}return result;
}
static void slider(U16 index,char *name,S16 x,S16 y,S16 w,S16 h,sGuiWindow *scroll)
{
 U16 j;static char *names[2][5]={{"GAIN_ADD","GAIN_SUB","GAIN_THUMB","GAIN_PAGEADD","GAIN_PAGESUB"},{"FS_ADD","FS_SUB","FS_THUMB","FS_PAGEADD","FS_PAGESUB"}};
 sGuiSlider *s=&sliders[index];rect(&s->mInfo,eGUI_TYPE_SLIDER,name,x,y,w,h);
 s->mButtonSize=12;s->mSizeMin=16;s->mSliderType=index?eGUI_SLIDER_VERTICAL:eGUI_SLIDER_HORIZONTAL;
 s->mpWindow=scroll;if(!scroll){s->mInfo.mpValue=&gainValue;s->mpLineSize=&vars[3];s->mpPageSize=&vars[4];}
 for(j=0;j<5;++j){sGuiButton *b=button(names[index][j],j==0?(index?"^":">"):j==1?(index?"v":"<"):"",0,0,0,0,j==2?3:0,eGUI_BUTTON_NONE);b->mString.mAlign.mH=eGUI_ALIGNH_CENTRE;s->mpButtons[j]=b;}
}
static void build(void)
{
 U16 i; sGuiButton *b;sGuiInfo **controls;U16 n=0;
 for(i=0;i<16;++i)colours[i].mPalIndex=(U8)i;
 /* main, raised, pressed, edit, title, track, highlighted */
 {U16 base[7]={2,3,5,0,5,0,5};for(i=0;i<7;++i)fills[i].mpColours[0]=&colours[base[i]];}
 fills[1].mpColours[1]=&colours[4];fills[1].mpColours[3]=&colours[0];
 fills[2].mpColours[1]=&colours[0];fills[2].mpColours[3]=&colours[4];
 fills[3].mpColours[1]=&colours[0];fills[3].mpColours[3]=&colours[3];
 for(i=0;i<5;++i){styles[i].mpFillNormal=&fills[1];styles[i].mpFillSelected=&fills[2];styles[i].mpFillLocked=&fills[1];}
 styles[1].mpFillNormal=styles[1].mpFillSelected=&fills[0];
 styles[2].mpFillNormal=&fills[3];styles[3].mpFillNormal=&fills[6];styles[4].mpFillNormal=styles[4].mpFillSelected=&fills[4];
 fontAsset.mpData=font;fontGroup.mpNormal=fontGroup.mpSelected=fontGroup.mpLocked=&fontAsset;
 cursorSprite.mpMask=Gui_CursorData;cursorSprite.mpGfx=Gui_CursorData+16;cursorSprite.mWidth=cursorSprite.mHeight=16;cursorSprite.mGfxPlaneCount=cursorSprite.mMaskPlaneCount=4;
 cursorBlock.mHeader.mSpriteCount=1;cursorBlock.mpSprite[0]=&cursorSprite;cursorAsset.mpData=&cursorBlock;cursor.mpAsset=&cursorAsset;
 rect(&windows[0].mInfo,eGUI_TYPE_WINDOW,"DESKTOP",0,0,320,200);
 rect(&windows[1].mInfo,eGUI_TYPE_WINDOW,"DEMO",12,28,296,158);
 rect(&windows[2].mInfo,eGUI_TYPE_WINDOW,"WND_FS",20,14,280,174);
 rect(&windows[3].mInfo,eGUI_TYPE_WINDOW,"WND_FILELIST",8,62,246,76);
 for(i=0;i<4;++i){windows[i].mpFill=&fills[0];windows[i].mpFontGroup=&fontGroup;windows[i].mpButtonStyle=&styles[0];windows[i].mCanvas=windows[i].mInfo.mRectPair.mLocal;windows[i].mCanvas.mX=windows[i].mCanvas.mY=0;}
 windows[0].mppControls=rootControls;windows[0].mControlCount=3;
 rootControls[0]=&button("TITLE","GODLIB / NATIVE GUI",12,4,292,16,4,eGUI_BUTTON_NONE)->mInfo;
 rootControls[1]=&windows[1].mInfo;
 rootControls[2]=&button("FOOTER","MOUSE + KEYBOARD / ENTER TO ACCEPT",12,187,296,10,1,eGUI_BUTTON_NONE)->mInfo;
 controls=demoControls;
 controls[n++]=&button("DEMO_TITLE","CONTROL PANEL",8,3,276,12,4,eGUI_BUTTON_NONE)->mInfo;
 controls[n++]=&button("NAME_LABEL","NAME",10,25,58,16,1,eGUI_BUTTON_NONE)->mInfo;
 b=button("NAME","",72,25,208,16,2,eGUI_BUTTON_TEXTLINE);bindString(b,"DEMO\\NAME");controls[n++]=&b->mInfo;
 controls[n++]=&button("GAIN_LABEL","LEVEL",10,59,58,14,1,eGUI_BUTTON_NONE)->mInfo;
 slider(0,"GAIN",72,59,164,14,0);controls[n++]=&sliders[0].mInfo;
 b=button("GAIN_VALUE","",242,59,38,14,2,eGUI_BUTTON_NONE);b->mString.mVar.mpName="DEMO\\GAIN";b->mString.mVar.mType=eGUI_VAR_S32;controls[n++]=&b->mInfo;
 controls[n++]=&button("APPLY","APPLY",10,91,72,18,0,eGUI_BUTTON_SPRING)->mInfo;
 controls[n++]=&button("RESET","RESET",88,91,72,18,0,eGUI_BUTTON_SPRING)->mInfo;
 controls[n++]=&button("OPEN","FILES...",166,91,80,18,3,eGUI_BUTTON_SPRING)->mInfo;
 b=button("EXIT","X",252,91,28,18,0,eGUI_BUTTON_SPRING);b->mpOnLeftClick=&exitAction;exitAction.mAction=eGUI_ACTION_APP_EXIT;controls[n++]=&b->mInfo;
 b=button("STATUS","",10,125,270,14,2,eGUI_BUTTON_NONE);bindString(b,"DEMO\\STATUS");controls[n++]=&b->mInfo;
 windows[1].mppControls=controls;windows[1].mControlCount=n;
 n=0;controls=fsControls;
 b=button("FS_TITLE","",6,2,264,13,4,eGUI_BUTTON_NONE);bindString(b,"GUI\\FS\\TITLE");controls[n++]=&b->mInfo;
 b=button("BUTT_DRIVE","",6,22,22,13,2,eGUI_BUTTON_TEXTLINE);bindString(b,"GUI\\FS\\DRIVE");controls[n++]=&b->mInfo;
 b=button("BUTT_FILEPATH","",32,22,194,13,2,eGUI_BUTTON_TEXTLINE);bindString(b,"GUI\\FS\\FILEPATH");controls[n++]=&b->mInfo;
 controls[n++]=&button("BUTT_FOLDERBACK","UP",230,22,40,13,0,eGUI_BUTTON_SPRING)->mInfo;
 b=button("BUTT_FILENAME","",6,42,188,14,2,eGUI_BUTTON_TEXTLINE);bindString(b,"GUI\\FS\\FILENAME");controls[n++]=&b->mInfo;
 b=button("BUTT_FILEMASK","",198,42,72,14,2,eGUI_BUTTON_TEXTLINE);bindString(b,"GUI\\FS\\FILEMASK");controls[n++]=&b->mInfo;
 windows[3].mpFill=&fills[3];controls[n++]=&windows[3].mInfo;
 slider(1,"FILE_SCROLL",254,62,16,76,&windows[3]);controls[n++]=&sliders[1].mInfo;
 closeAction.mpWindowClose=&windows[2];
 b=button("BUTT_FS_OK","SELECT",38,146,88,18,3,eGUI_BUTTON_SPRING);b->mpOnLeftClick=&closeAction;controls[n++]=&b->mInfo;
 b=button("BUTT_FS_CANCEL","CANCEL",142,146,88,18,0,eGUI_BUTTON_SPRING);b->mpOnLeftClick=&closeAction;controls[n++]=&b->mInfo;
 windows[2].mppControls=controls;windows[2].mControlCount=n;
 data.mpWindows=windows;data.mWindowCount=4;data.mpButtons=buttons;data.mButtonCount=buttonCount;data.mpSliders=sliders;data.mSliderCount=2;data.mpCursors=&cursor;data.mCursorCount=1;
}
void __attribute__((noinline)) GuiExample_Frame(void){__asm__ volatile("" ::: "memory");}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 U16 i;S16 error=0; sString *p;(void)argc;(void)argv;
 GemDos_Super(0);Platform_Init();Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);
 if(!Screen_GetpMemBase()){Platform_DeInit();return 1;}
 HashTree_Init(&tree);String_Init(&gGuiName,"ATARI");String_Init(&statusText,"TRY THE CONTROLS AND FILE SELECTOR");
 var(0,"DEMO\\GAIN",50);var(1,"DEMO\\MIN",0);var(2,"DEMO\\MAX",100);var(3,"DEMO\\STEP",1);var(4,"DEMO\\PAGE",10);
 p=&gGuiName;HashTree_Var_Init(&values[5],&tree,"DEMO\\NAME",sizeof(p),&p);HashTree_VarWrite(&values[5],&p);
 p=&statusText;HashTree_Var_Init(&values[6],&tree,"DEMO\\STATUS",sizeof(p),&p);HashTree_VarWrite(&values[6],&p);
 gainValue.mpVar=&vars[0];gainValue.mpValueMin=&vars[1];gainValue.mpValueMax=&vars[2];
 font=makeFont();if(!font){error=1;goto cleanup;}
 build();Gui_Init(&tree);GuiFS_Init(&tree);RenderGui_Init();
 GuiFSInfo_Init(&selector,"CHOOSE A DOCUMENT","*.TXT","");String_Set(&selector.mFilePath,"DATA");selector.mpCB=selected;
 for(i=0;i<3;++i){static char *names[]={"GUI\\BUTTONS\\APPLY","GUI\\BUTTONS\\RESET","GUI\\BUTTONS\\OPEN"};clients[i].mUserData=i;HashTree_VarClient_Init(&clients[i],&tree,names[i],clicked);}
 Gui_DataAdd(&data);IKBD_SetMousePosition(160,100);Fade_SetPalDirect(palette);gGuiReady=1;
 while(Gui_Update()){
  Screen_Update();IKBD_Update();RenderGui_Update(Screen_GetpLogicGraphic());
  HashTree_VarRead(&values[0],(void*)&gGuiGain,4);gGuiListCount=windows[3].mControlCount;gGuiScrollY=windows[3].mCanvas.mY;gGuiTreeCount=countVars();
  gGuiMouseX=Gui_GetpMouse()->mX;gGuiMouseY=Gui_GetpMouse()->mY;
  ++gGuiFrame;GuiExample_Frame();
 }
 for(i=0;i<3;++i)HashTree_VarClient_DeInit(&clients[i],&tree);
 GuiFSInfo_DeInit(&selector);GuiFS_DeInit(&tree);Gui_DataRemove(&data);RenderGui_DeInit();Gui_DeInit();
cleanup:
 for(i=0;i<5;++i)HashTree_VarClient_DeInit(&vars[i].mVarClient,&tree);
 for(i=0;i<7;++i)HashTree_Var_DeInit(&values[i],&tree);
 String_DeInit(&gGuiName);String_DeInit(&statusText);gGuiCleanupVars=countVars();HashTree_DeInit(&tree);
 if(font)Font_Destroy(font);
 Screen_DeInit();Platform_DeInit();gGuiExited=1;return error;
}
