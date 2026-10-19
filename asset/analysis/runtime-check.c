#include <godlib/linkfile/linkfile.h>
#include <godlib/asset/asset.h>
#include <godlib/asset/context.h>
#include <godlib/platform/platform.h>
#include <godlib/screen/screen.h>
#include <godlib/ikbd/ikbd.h>
#include <godlib/fade/fade.h>
#include <godlib/font8x8/font8x8.h>
#include <godlib/gemdos/gemdos.h>
#include <godlib/memory/memory.h>
#include <godlib/packer/packer.h>
#include <godlib/packer/godpack.h>
#include <string.h>
#include <stdio.h>
volatile U16 gAssetTestDone,gAssetTestPass,gAssetTestStage;
#define CHECK(expr,id) do{gAssetTestStage=id;if(!(expr))return 0;}while(0)
static U16 loads[3],unloads[3];static U32 payload=0x12345678UL;
static U32 loaded(void *data,U32 size,U32 id){if(data!=&payload||size!=4)return 0;++loads[id];return 1;}
static U32 unloaded(void *data,U32 size,U32 id){if(data!=&payload||size!=4)return 0;++unloads[id];return 1;}
static U16 tests(void)
{
 sLinkFile *disk,*ram,*packed;U8 *raw,*compressed,*decoded,*expected,*copy,*member;S32 size;U16 i;sContext context;sAssetClient clients[3];void *slots[3]={0,0,0};sAssetItem item;char path[40];
 const char *names[]={"CASTLE.PI1","FONT.BFB","SPARKS.BSB"};U32 baseline=Memory_GetFree();
 CHECK(!LinkFile_Init("ABSENT.LNK")&&!LinkFile_InitToRAM("ABSENT.LNK"),1);
 raw=File_Load("DATA\\SCENE.LNK");compressed=File_Load("DATA\\PACKED.LNK");CHECK(raw&&compressed,2);
 size=File_GetSize("DATA\\SCENE.LNK");CHECK(Packer_IsPacked((sPackerHeader*)compressed)&&Packer_GetDepackSize((sPackerHeader*)compressed)==(U32)size,3);
 decoded=(U8*)mMEMALLOC((U32)size+dGODPACK_OVERFLOW);CHECK(decoded,4);Packer_Depack(compressed,decoded);CHECK(!memcmp(raw,decoded,(U32)size),5);
 mMEMFREE(decoded);File_UnLoad(raw);File_UnLoad(compressed);
 disk=LinkFile_Init("DATA\\SCENE.LNK");ram=LinkFile_InitToRAM("DATA\\SCENE.LNK");packed=LinkFile_InitToRAM("DATA\\PACKED.LNK");CHECK(disk&&ram&&packed,6);
 CHECK(!disk->mInRamFlag&&ram->mInRamFlag&&packed->mInRamFlag&&disk->mTotalFileCount==3,7);
 CHECK(!LinkFile_FileExists(disk,"ABSENT.BSB")&&!LinkFile_FileLoad(ram,"ABSENT.BSB",0,0),8);
 for(i=0;i<3;++i){
  snprintf(path,sizeof(path),"UNLINK\\SCENE\\%s",names[i]);size=File_GetSize(path);expected=File_Load(path);CHECK(expected&&size>0,9+i*4);
  CHECK(LinkFile_FileExists(disk,(char*)names[i])&&LinkFile_FileGetSize(disk,(char*)names[i],0)==size&&LinkFile_FileGetSize(disk,(char*)names[i],1)==size,10+i*4);
  member=LinkFile_FileLoad(disk,(char*)names[i],1,0);CHECK(member&&!memcmp(member,expected,(U32)size),11+i*4);mMEMFREE(member);
  member=LinkFile_FileLoad(ram,(char*)names[i],0,0);copy=(U8*)mMEMALLOC((U32)size);
  CHECK(member&&(U32)member>(U32)ram&&!memcmp(member,expected,(U32)size)&&LinkFile_FileLoadAt(packed,(char*)names[i],copy,0)&&!memcmp(copy,expected,(U32)size),12+i*4);
  mMEMFREE(copy);File_UnLoad(expected);
 }
 LinkFile_DeInit(disk);LinkFile_DeInit(ram);LinkFile_DeInit(packed);CHECK(Memory_GetFree()==baseline,21);
 Context_Init(&context,"CLIENTTEST");Memory_Clear(sizeof(clients),clients);Memory_Clear(sizeof(item),&item);item.mpData=&payload;item.mSize=4;
 for(i=0;i<3;++i){clients[i].OnLoad=loaded;clients[i].OnUnLoad=unloaded;clients[i].mUserData=i;AssetClient_Init(&clients[i],"SHARED.BFB","CLIENTTEST",&slots[i]);}
 CHECK(context.mRefCount==3,22);CHECK(AssetClients_OnLoad(&clients[0],&item)&&slots[0]==&payload&&slots[1]==slots[0]&&slots[2]==slots[0],23);
 CHECK(loads[0]==1&&loads[1]==1&&loads[2]==1,24);
 CHECK(AssetClients_OnUnLoad(&clients[0])&&!slots[0]&&!slots[1]&&!slots[2]&&unloads[0]==1&&unloads[1]==1&&unloads[2]==1,25);
 /* Chain is head 0 -> 2 -> 1. Remove the deep tail, then promote child 2. */
 AssetClient_DeInit(&clients[1]);CHECK(context.mRefCount==2&&clients[0].mpNext==&clients[2]&&!clients[2].mpNext,26);
 AssetClient_DeInit(&clients[0]);CHECK(context.mRefCount==1&&Context_AssetClient_Find(&context,clients[2].mHashKey)==&clients[2],27);
 AssetClient_DeInit(&clients[2]);CHECK(context.mRefCount==0&&!context.mpAssetClients,28);Context_DeInit(&context);
 return 1;
}
S16 GodLib_Game_Main(S16 argc,char **argv)
{
 static U16 pal[16]={0,0x777};U16 dirty=2;char line[40];(void)argc;(void)argv;
 GemDos_Super(0);Platform_Init();Screen_Init(320,200,eGRAPHIC_COLOURMODE_4PLANE,0);Fade_SetPalDirect(pal);
 gAssetTestPass=tests();gAssetTestDone=1;
 while(!IKBD_GetKeyStatus(eIKBDSCAN_ESC)){Screen_Update();if(dirty){Screen_Logic_ClearScreen();sprintf(line,"ASSET %s / CHECK %u",gAssetTestPass?"PASS":"FAIL",gAssetTestStage);Font8x8_Print(line,Screen_GetpLogic(),0,16);--dirty;}}
 Screen_DeInit();Platform_DeInit();return !gAssetTestPass;
}
