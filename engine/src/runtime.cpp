#include "qe/runtime.h"
#include <algorithm>
#include <cstdint>
namespace qe {
Runtime::Runtime(App& app, Platform& platform, Config config)
    :app_(app),platform_(platform),config_(config) {}
bool Runtime::start(uint32_t now_ms) {
    if (started_ || config_.fixed_step_ms==0 || config_.fixed_step_ms>1000 ||
        config_.max_catchup_steps==0 || config_.max_catchup_steps>16 ||
        config_.viewport_width!=platform_.width() ||
        config_.viewport_height!=platform_.height())return false;
    stats_=Stats{}; size_=head_=accumulator_ms_=0;
    last_ms_=now_ms; paused_=false; started_=true;
    app_.init(platform_);
    app_.draw(platform_);platform_.present();++stats_.renders;
    return true;
}
bool Runtime::queue(KeyEvent event) {
    if(!started_)return false;
    if(event.key==Key::Menu || event.key==Key::SelectLong) {
        platform_.reservedSystemKey(event);
        return false;
    }
    if(paused_)return false;
    if(size_==INPUT_CAPACITY){++stats_.input_overflows;return false;}
    queue_[(head_+size_)%INPUT_CAPACITY]=event;
    ++size_;
    return true;
}
void Runtime::dispatch(){
    while(size_) {
        const auto event=queue_[head_];
        head_=(head_+1)%INPUT_CAPACITY;--size_;
        app_.onKey(event);
    }
}
void Runtime::tick(uint32_t now_ms){
    if(!started_)return;
    if(paused_){last_ms_=now_ms;return;}
    const uint32_t elapsed=now_ms-last_ms_;
    last_ms_=now_ms;
    const bool had_input=(size_!=0);
    dispatch();
    const uint32_t budget=config_.fixed_step_ms*config_.max_catchup_steps;
    const uint32_t capacity=budget>accumulator_ms_ ? budget-accumulator_ms_:0;
    const uint32_t accepted=std::min(elapsed,capacity);
    stats_.dropped_ms+=(uint64_t)elapsed-accepted;
    accumulator_ms_+=accepted;
    uint32_t ran=0;
    while(accumulator_ms_>=config_.fixed_step_ms && ran<config_.max_catchup_steps){
        app_.update(config_.fixed_step_ms);
        accumulator_ms_-=config_.fixed_step_ms;
        ++stats_.updates;++ran;
    }
    if(ran||had_input){app_.draw(platform_);platform_.present();++stats_.renders;}
}
void Runtime::pause(){
    if(!started_ || paused_)return;
    paused_=true;size_=0;head_=0;accumulator_ms_=0;
    app_.pause();
}
void Runtime::resume(uint32_t now_ms){
    if(!started_ || !paused_)return;
    last_ms_=now_ms;paused_=false;accumulator_ms_=0;
    app_.resume();
    app_.draw(platform_);platform_.present();++stats_.renders;
}
void Runtime::stop(){
    if(!started_)return;
    started_=false;size_=0;accumulator_ms_=0;
    app_.shutdown();
}
}
