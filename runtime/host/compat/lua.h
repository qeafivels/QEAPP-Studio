/* TEST-ONLY declarations for the system-provided Lua 5.4 shared library.
 * These are NOT part of target firmware. The target must use the exact vendor headers.
 * Cross-check ABI at test time against LUA_VERSION_NUM and an actual Lua version.
 */
#ifndef QE_HOST_LUA_COMPAT_H
#define QE_HOST_LUA_COMPAT_H
#include <stddef.h>
#define LUA_VERSION_NUM 504
#define LUA_REGISTRYINDEX (-1001000)
#define LUA_MASKCOUNT 8
#define LUA_OK 0
#define LUA_MULTRET (-1)
#define LUA_TNIL 0
#ifdef __cplusplus
extern "C" {
#endif
typedef struct lua_State lua_State;
typedef struct lua_Debug lua_Debug;
typedef long long lua_Integer;
typedef double lua_Number;
typedef void *(*lua_Alloc)(void *, void *, size_t, size_t);
typedef int (*lua_CFunction)(lua_State *);
typedef void (*lua_Hook)(lua_State *, lua_Debug *);
typedef long long lua_KContext;
typedef int (*lua_KFunction)(lua_State *, int, lua_KContext);
lua_State *lua_newstate(lua_Alloc, void *);
void lua_close(lua_State *);
void lua_settop(lua_State *,int);
int lua_gettop(lua_State *);
int lua_type(lua_State *,int);
const char *lua_tolstring(lua_State *,int,size_t *);
lua_Integer lua_tointegerx(lua_State *,int,int *);
void lua_pushnumber(lua_State *,lua_Number);
void lua_pushboolean(lua_State *,int);
void lua_pushnil(lua_State *);
void lua_pushlightuserdata(lua_State *,void *);
void lua_pushcclosure(lua_State *,lua_CFunction,int);
int lua_getglobal(lua_State *,const char *);
void lua_setglobal(lua_State *,const char *);
int lua_getfield(lua_State *,int,const char *);
void lua_setfield(lua_State *,int,const char *);
void *lua_touserdata(lua_State *,int);
void lua_createtable(lua_State *,int,int);
int lua_pcallk(lua_State *,int,int,int,lua_KContext,lua_KFunction);
int lua_sethook(lua_State *,lua_Hook,int,int);
void lua_rotate(lua_State *,int,int);
const char *lua_pushstring(lua_State *,const char *);
int lua_error(lua_State *);
#ifdef __cplusplus
}
#endif
#define lua_pop(L,n) lua_settop(L,-(n)-1)
#define lua_pushcfunction(L,f) lua_pushcclosure(L,(f),0)
#define lua_newtable(L) lua_createtable(L,0,0)
#define lua_tostring(L,i) lua_tolstring(L,i,NULL)
#define lua_pcall(L,a,b,c) lua_pcallk(L,a,b,c,0,NULL)
#endif
