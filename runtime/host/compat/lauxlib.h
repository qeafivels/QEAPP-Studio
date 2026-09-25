#ifndef QE_HOST_LUA_AUXLIB
#define QE_HOST_LUA_AUXLIB
#include "lua.h"
#ifdef __cplusplus
extern "C" {
#endif
int luaL_loadbufferx(lua_State *,const char *,size_t,const char *,const char *);
lua_Integer luaL_checkinteger(lua_State *,int);
const char *luaL_checklstring(lua_State *,int,size_t *);
void luaL_requiref(lua_State *,const char *,lua_CFunction,int);
#ifdef __cplusplus
}
#endif
#endif
