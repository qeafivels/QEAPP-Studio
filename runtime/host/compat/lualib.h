#ifndef QE_HOST_LUA_LIB
#define QE_HOST_LUA_LIB
#include "lua.h"
#ifdef __cplusplus
extern "C" {
#endif
int luaopen_base(lua_State *);
int luaopen_math(lua_State *);
int luaopen_table(lua_State *);
int luaopen_string(lua_State *);
int luaopen_utf8(lua_State *);
#ifdef __cplusplus
}
#endif
#endif
