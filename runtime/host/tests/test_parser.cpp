#include "QeappFormat.h"
#include <cstring>
#include <iostream>
int main() {
  using namespace Qeapp;
  Meta meta;const char *reason="";
  const char lua[]="id=lua_hello\nname=Lua Hello\nversion=0.1.0\ntype=lua\n";
  const char rejectEntry[]="id=lua_hello\nname=Lua Hello\nversion=0.1.0\ntype=lua\nentry=oops\n";
  const char text[]="id=notes\nname=Notes\nversion=1.0\ntype=text\n";
  bool validText=parseManifest(text,sizeof(text)-1,meta,reason);
  bool validLua=parseManifest(lua,sizeof(lua)-1,meta,reason);
#ifdef VQEAF_ENABLE_LUA
  if (!validText || !validLua || std::strcmp(meta.type,"lua")) return 1;
  if (parseManifest(rejectEntry,sizeof(rejectEntry)-1,meta,reason)) return 2;
#else
  if (!validText || validLua) return 3;
#endif
  std::cout<<"PASS parser beta="
#ifdef VQEAF_ENABLE_LUA
  <<1
#else
  <<0
#endif
  <<"\n";
}
