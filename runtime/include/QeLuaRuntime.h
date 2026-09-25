#pragma once
#include <stddef.h>
#include <stdint.h>

// Shared C++17/C++11 API: no Arduino and no desktop Qt dependency.
// Lua 5.4 is provided by the official, hash-checked source bundle (see bootstrap_lua.py).
struct lua_State;
class QeLuaRuntime {
public:
  struct Draw {
    void (*rect)(void *user, int x, int y, int w, int h, uint16_t rgb565);
    void (*text)(void *user, int x, int y, const char *value, uint16_t rgb565);
    uint32_t (*millis)(void *user);
    void *user;
  };
  QeLuaRuntime();
  ~QeLuaRuntime();
  QeLuaRuntime(const QeLuaRuntime&) = delete;
  QeLuaRuntime &operator=(const QeLuaRuntime&) = delete;
  // Script must already be loaded from a cryptographically verified installed package.
  // This VM does not make unsigned code trustworthy or replace installer signature checks.
  bool start(const char *source, size_t sourceBytes, const Draw &draw,
             size_t heapLimit = 192 * 1024);
  bool update(float seconds);    // Calls on_update(dt) when present.
  bool render();                 // Calls on_draw() when present.
  bool key(const char *name, bool down); // Calls on_key(name, down) when present.
  void stop();
  bool running() const { return L_ != nullptr; }
  size_t heapUsed() const { return memUsed_; }
  size_t peakHeapUsed() const { return peakUsed_; }
  const char *error() const { return error_; }
  static constexpr size_t kMaxSource = 64 * 1024;
  static constexpr unsigned kInstructionsPerCall = 75000;
  static constexpr uint32_t kDeadlineMs = 65;
  static constexpr unsigned kDrawCallsPerCallback = 512;
private:
  static void *alloc(void *ud, void *ptr, size_t old, size_t now);
  static void hook(lua_State *L, struct lua_Debug *debug);
  static QeLuaRuntime *self(lua_State *L);
  static void drawBudget(lua_State *L, QeLuaRuntime *vm);
  static int lRect(lua_State *L);
  static int lText(lua_State *L);
  static int lClear(lua_State *L);
  static int lBlit1(lua_State *L);
  static int lHeapUsed(lua_State *L);
  static int lHeapPeak(lua_State *L);
  void setError(const char *message);
  bool invoke(const char *name, int args);
  lua_State *L_;
  Draw draw_;
  size_t memUsed_, peakUsed_, heapLimit_;
  unsigned drawCalls_;
  unsigned instructions_;
  uint32_t deadlineAt_;
  bool timeout_;
  char error_[192];
};
