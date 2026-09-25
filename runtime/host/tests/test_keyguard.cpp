// Bypass the replay file reader intentionally; the VM itself must reject OS keys.
#include "QeLuaRuntime.h"
#include <cstring>
#include <cstdio>
#include <cstdint>
#include <chrono>
static uint32_t tick(void*) {
 using namespace std::chrono;
 return static_cast<uint32_t>(duration_cast<milliseconds>(steady_clock::now().time_since_epoch()).count());
}
static void rect(void*,int,int,int,int,uint16_t) {}
static void text(void*,int,int,const char*,uint16_t) {}
int main() {
 QeLuaRuntime vm;
 const QeLuaRuntime::Draw cb{rect,text,tick,nullptr};
 const char source[]="function on_key(name, down) end";
 if(!vm.start(source,sizeof(source)-1,cb)) return 2;
 if(!vm.key("up",true)) return 3;
 if(vm.key("menu",true)) return 4;
 if(vm.running() || !strstr(vm.error(),"reserved")) return 5;
 if(!vm.start(source,sizeof(source)-1,cb)) return 6;
 if(vm.key(nullptr,true)) return 7;
 if(vm.running()) return 8;
 std::puts("PASS: VM keyguard rejects menu and null keys");
 return 0;
}
