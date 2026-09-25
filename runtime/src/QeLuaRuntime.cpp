#include "QeLuaRuntime.h"
#include "lua.h"
#include "lauxlib.h"
#include "lualib.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#ifdef QE_LUA_PSRAM_ALLOC
#include <esp_heap_caps.h>
#endif

QeLuaRuntime::QeLuaRuntime() : L_(nullptr), draw_{nullptr,nullptr,nullptr,nullptr},
  memUsed_(0), peakUsed_(0), heapLimit_(0), drawCalls_(0), instructions_(0), deadlineAt_(0), timeout_(false), error_{0} {}
QeLuaRuntime::~QeLuaRuntime() { stop(); }
void QeLuaRuntime::setError(const char *message) {
  snprintf(error_, sizeof(error_), "%s", message ? message : "unknown Lua error");
}
void *QeLuaRuntime::alloc(void *ud, void *ptr, size_t old, size_t now) {
  auto *vm = static_cast<QeLuaRuntime *>(ud);
  if (!ptr) old=0; // Lua uses osize as a type tag when ptr == nullptr.
  if (!now) {
    if (ptr) {
#ifdef QE_LUA_PSRAM_ALLOC
      heap_caps_free(ptr);
#else
      free(ptr);
#endif
      vm->memUsed_ = old > vm->memUsed_ ? 0 : vm->memUsed_ - old;
    }
    return nullptr;
  }
  if (ptr && old > vm->memUsed_) return nullptr;
  if (vm->memUsed_ > vm->heapLimit_ ||
      (now > old && now-old > vm->heapLimit_ - vm->memUsed_)) return nullptr;
#ifdef QE_LUA_PSRAM_ALLOC
  void *next = ptr ? heap_caps_realloc(ptr,now,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT)
                   : heap_caps_malloc(now,MALLOC_CAP_SPIRAM|MALLOC_CAP_8BIT);
#else
  void *next = realloc(ptr,now);
#endif
  if (next) {
    vm->memUsed_ = vm->memUsed_ - old + now;
    if (vm->memUsed_ > vm->peakUsed_) vm->peakUsed_ = vm->memUsed_;
  }
  return next;
}
QeLuaRuntime *QeLuaRuntime::self(lua_State *L) {
  lua_getfield(L,LUA_REGISTRYINDEX,"__vqeaf_runtime");
  auto *vm = static_cast<QeLuaRuntime *>(lua_touserdata(L,-1));
  lua_pop(L,1);
  return vm;
}
void QeLuaRuntime::hook(lua_State *L, lua_Debug *) {
  QeLuaRuntime *vm=self(L);
  if (!vm) return;
  vm->instructions_ += 1000;
  const uint32_t now = vm->draw_.millis ? vm->draw_.millis(vm->draw_.user) : 0;
  if (vm->instructions_ > kInstructionsPerCall ||
      (vm->draw_.millis && (int32_t)(now - vm->deadlineAt_) > 0)) {
    vm->timeout_ = true;
    lua_pushstring(L,"Lua execution budget exceeded");
    lua_error(L);
  }
}
// The hook must throw a Lua error from C, never throw a C++ exception through Lua.
// Keep all clipping arithmetic in lua_Integer. Casting untrusted Lua numbers to
// 32-bit int BEFORE clipping could overflow and make a bogus TFT rectangle.
static int qe_clip(lua_Integer n, int low, int high) {
  return n < low ? low : (n > high ? high : static_cast<int>(n));
}
static uint16_t qe_color(lua_State *L, int index) {
  const lua_Integer value = luaL_checkinteger(L,index);
  if (value < 0 || value > 65535) {
    lua_pushstring(L,"RGB565 color must be in range 0..65535");
    lua_error(L);
    return 0;
  }
  return static_cast<uint16_t>(value);
}
void QeLuaRuntime::drawBudget(lua_State *L, QeLuaRuntime *vm) {
  // This is a C callback called only after a successful runtime lookup.
  if (!vm) return;
  // drawCalls is reset on every top-level / update / render / key callback.
  // Never hand scripts unlimited SPI draw operations even when instructions
  // and wall-clock hook budgets are under their limits.
  if (++vm->drawCalls_ > QeLuaRuntime::kDrawCallsPerCallback) {
    lua_pushstring(L,"Lua draw call budget exceeded");
    lua_error(L);
  }
}
int QeLuaRuntime::lRect(lua_State *L) {
  auto *vm=self(L);
  const lua_Integer x=luaL_checkinteger(L,1), y=luaL_checkinteger(L,2);
  const lua_Integer w=luaL_checkinteger(L,3), h=luaL_checkinteger(L,4);
  const uint16_t color=qe_color(L,5);
  if (vm && vm->draw_.rect && w>0 && h>0 && w<=240 && h<=270 &&
      x<240 && y<270 && x>-w && y>-h) {
    const int x1=qe_clip(x,0,240), y1=qe_clip(y,0,270);
    // x + w and y + h are now proven bounded: x > -w and x < 240.
    const int x2=qe_clip(x+w,0,240), y2=qe_clip(y+h,0,270);
    if (x2>x1 && y2>y1) {
      drawBudget(L,vm);
      vm->draw_.rect(vm->draw_.user,x1,y1,x2-x1,y2-y1,color);
    }
  }
  return 0;
}
int QeLuaRuntime::lText(lua_State *L) {
  auto *vm=self(L);
  const lua_Integer x=luaL_checkinteger(L,1), y=luaL_checkinteger(L,2);
  size_t len=0;const char *s=luaL_checklstring(L,3,&len);
  const uint16_t color=qe_color(L,4);
  if (vm && vm->draw_.text && x>=0 && x<240 && y>=0 && y<270 &&
      len>0 && len<=48 && !memchr(s,0,len)) {
    drawBudget(L,vm);
    vm->draw_.text(vm->draw_.user,static_cast<int>(x),static_cast<int>(y),s,color);
  }
  return 0;
}
int QeLuaRuntime::lClear(lua_State *L) {
  auto *vm=self(L);
  const uint16_t color=qe_color(L,1);
  if (vm && vm->draw_.rect) {
    drawBudget(L,vm);
    vm->draw_.rect(vm->draw_.user,0,0,240,270,color);
  }
  return 0;
}
// Portable 1-bit sprite: row-major MSB-first bits, transparent zero bits.
// The sprite is embedded in the signed Lua source; no arbitrary path/network IO.
// Split visible runs into rectangles and check the *entire* draw budget before
// the first rectangle is submitted. This prevents half-drawn malformed sprites.
static int qe_fail(lua_State *L,const char *message) {lua_pushstring(L,message);return lua_error(L);}
int QeLuaRuntime::lBlit1(lua_State *L) {
  auto *vm=self(L);
  const lua_Integer x=luaL_checkinteger(L,1), y=luaL_checkinteger(L,2);
  const lua_Integer width=luaL_checkinteger(L,3), height=luaL_checkinteger(L,4);
  size_t length=0;
  const unsigned char *bits=reinterpret_cast<const unsigned char *>(luaL_checklstring(L,5,&length));
  const uint16_t color=qe_color(L,6);
  if (width<1 || height<1 || width>32 || height>32 ||
      length!=static_cast<size_t>((width*height+7)/8)) {
    return qe_fail(L,"blit1: width/height 1..32 and exact packed payload required");
  }
  const size_t count=static_cast<size_t>(width*height);
  if ((count%8) && (bits[length-1] & ((1U<<(8-(count%8)))-1U))) {
    return qe_fail(L,"blit1: non-zero trailing padding bits");
  }
  if (!vm || !vm->draw_.rect || x>=240 || y>=270 ||
      x<=-width || y<=-height) return 0;
  // The tested visibility bounds prove x+width/y+height cannot overflow a
  // lua_Integer (dimensions <= 32). Coordinates then clip to 240x270.
  const int xmin=qe_clip(x,0,240), xmax=qe_clip(x+width,0,240);
  const int ymin=qe_clip(y,0,270), ymax=qe_clip(y+height,0,270);
  auto pixel=[&](int sx,int sy)->bool {
    const size_t b=static_cast<size_t>(sy)*static_cast<size_t>(width)+static_cast<size_t>(sx);
    return (bits[b>>3] & (0x80U>>(b&7)))!=0;
  };
  // Two scans: validation cannot leave a partially drawn sprite after an
  // exhausted budget. No dynamic allocations, same primitive on host/device.
  for (int phase=0;phase<2;++phase) {
    unsigned needed=0;
    for (int sy=0;sy<static_cast<int>(height);++sy) {
      const int dy=static_cast<int>(y+sy);
      if (dy<ymin || dy>=ymax) continue;
      int sx=0;
      while(sx<static_cast<int>(width)) {
        while(sx<static_cast<int>(width) && !pixel(sx,sy)) ++sx;
        const int start=sx;
        while(sx<static_cast<int>(width) && pixel(sx,sy)) ++sx;
        if(start==sx) break;
        const int left=qe_clip(x+start,xmin,xmax),right=qe_clip(x+sx,xmin,xmax);
        if(right<=left)continue;
        if(phase==1) vm->draw_.rect(vm->draw_.user,left,dy,right-left,1,color);
        ++needed;
      }
    }
    if (phase==0) {
      if(needed>kDrawCallsPerCallback || vm->drawCalls_>kDrawCallsPerCallback-needed)
        return qe_fail(L,"Lua draw call budget exceeded (blit1)");
      vm->drawCalls_+=needed;
    }
  }
  return 0;
}
int QeLuaRuntime::lHeapUsed(lua_State *L) {
  auto *vm=self(L);
  lua_pushnumber(L,vm ? static_cast<lua_Number>(vm->heapUsed()) : 0);
  return 1;
}
int QeLuaRuntime::lHeapPeak(lua_State *L) {
  auto *vm=self(L);
  lua_pushnumber(L,vm ? static_cast<lua_Number>(vm->peakHeapUsed()) : 0);
  return 1;
}
static void qe_require(lua_State *L,const char *name,lua_CFunction fn) {
  luaL_requiref(L,name,fn,1);
  lua_pop(L,1);
}
bool QeLuaRuntime::start(const char *source,size_t bytes,const Draw &draw,size_t heapLimit) {
  stop();error_[0]=0;peakUsed_=0;drawCalls_=0;
  if (!source || !bytes || bytes>kMaxSource || memchr(source,0,bytes) ||
      !draw.rect || !draw.text || !draw.millis || heapLimit<16*1024 || heapLimit>1024*1024) {
    setError("Invalid source/callbacks/budget");return false;
  }
  draw_=draw;heapLimit_=heapLimit;
  L_=lua_newstate(alloc,this);
  if (!L_) {setError("Lua VM allocation failed");return false;}
  lua_pushlightuserdata(L_,this);
  lua_setfield(L_,LUA_REGISTRYINDEX,"__vqeaf_runtime");
  // No io, os, package, debug, coroutine, native modules or unrestricted loaders.
  qe_require(L_,"_G",luaopen_base);
  qe_require(L_,"math",luaopen_math);
  qe_require(L_,"string",luaopen_string);
  qe_require(L_,"table",luaopen_table);
  qe_require(L_,"utf8",luaopen_utf8);
  const char *dangerous[]={"dofile","loadfile","load","collectgarbage","print",nullptr};
  for (const char **it=dangerous;*it;++it) {lua_pushnil(L_);lua_setglobal(L_,*it);}
  lua_getglobal(L_,"string");lua_pushnil(L_);lua_setfield(L_,-2,"dump");lua_pop(L_,1);
  lua_newtable(L_);
  lua_pushcfunction(L_,lRect);lua_setfield(L_,-2,"rect");
  lua_pushcfunction(L_,lText);lua_setfield(L_,-2,"text");
  lua_pushcfunction(L_,lClear);lua_setfield(L_,-2,"clear");
  lua_pushcfunction(L_,lBlit1);lua_setfield(L_,-2,"blit1");
  lua_pushcfunction(L_,lHeapUsed);lua_setfield(L_,-2,"heap_used");
  lua_pushcfunction(L_,lHeapPeak);lua_setfield(L_,-2,"heap_peak");
  lua_pushnumber(L_,240);lua_setfield(L_,-2,"width");
  lua_pushnumber(L_,270);lua_setfield(L_,-2,"height");
  lua_setglobal(L_,"engine");
  // Text chunks only: Lua precompiled bytecode is deliberately rejected.
  if (luaL_loadbufferx(L_,source,bytes,"@signed-qeapp-main.lua","t") != LUA_OK) {
    setError(lua_tostring(L_,-1));stop();return false;
  }
  instructions_=0;drawCalls_=0;timeout_=false;deadlineAt_=draw_.millis(draw_.user)+kDeadlineMs;
  lua_sethook(L_,hook,LUA_MASKCOUNT,1000);
  if (lua_pcall(L_,0,0,0)!=LUA_OK) {
    setError(timeout_?"Lua execution budget exceeded":lua_tostring(L_,-1));stop();return false;
  }
  return true;
}
bool QeLuaRuntime::invoke(const char *fn,int args) {
  // Place function below arguments supplied in reverse order by caller.
  if (!L_)return false;
  int argc=args;
  lua_getglobal(L_,fn);
  if (lua_type(L_,-1)==LUA_TNIL) {lua_pop(L_,argc+1);return true;}
  // Need function before args. Use lua_rotate (public Lua API).
  lua_rotate(L_,-argc-1,1);
  instructions_=0;drawCalls_=0;timeout_=false;deadlineAt_=draw_.millis(draw_.user)+kDeadlineMs;
  if (lua_pcall(L_,argc,0,0)==LUA_OK)return true;
  setError(timeout_?"Lua execution budget exceeded":lua_tostring(L_,-1));
  stop();return false;
}
bool QeLuaRuntime::update(float seconds) {
  if (!L_)return false;
  lua_pushnumber(L_,seconds<0?0:(seconds>0.1f?0.1f:seconds));
  return invoke("on_update",1);
}
bool QeLuaRuntime::render() {return invoke("on_draw",0);}
bool QeLuaRuntime::key(const char *name,bool down) {
  if (!L_) return false;
  // Defense in depth: OS-reserved keys cannot be injected even if caller
  // accidentally bypasses GUI/replay/firmware input filtering.
  const bool allowed = name &&
      (!strcmp(name,"up") || !strcmp(name,"down") ||
       !strcmp(name,"left") || !strcmp(name,"right") ||
       !strcmp(name,"start") || !strcmp(name,"option"));
  if (!allowed) {
    setError("OS-reserved or invalid Lua key");
    stop();
    return false;
  }
  lua_pushstring(L_,name);lua_pushboolean(L_,down);
  return invoke("on_key",2);
}
void QeLuaRuntime::stop() {
  if (L_) {lua_close(L_);L_=nullptr;}
  // Do not clear error_ here: retain a meaningful error for the UI.
  memUsed_=0;heapLimit_=0;
}
