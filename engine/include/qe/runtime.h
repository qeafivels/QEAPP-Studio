/* QEAPP Studio M1 HOST engine interface, NOT a firmware runtime or QEAPP ABI.
 * Portable C++17; no Arduino headers. No executable package support added.
 */
#ifndef QEAPP_STUDIO_QE_RUNTIME_H
#define QEAPP_STUDIO_QE_RUNTIME_H
#include <cstddef>
#include <cstdint>
namespace qe {

enum class Key : uint8_t {
    Up, Down, Left, Right, Ok, Back, Delete, Option, Menu, SelectLong
};
enum class KeyAction : uint8_t { Press, Release };
struct KeyEvent { Key key; KeyAction action; };

struct Sprite565 {
    const uint16_t* pixels;
    size_t pixel_count;
    uint16_t width;
    uint16_t height;
    uint16_t transparent_color;
    bool has_transparency;
};

class PixelSink {
public:
    virtual ~PixelSink() = default;
    virtual uint16_t width() const = 0;
    virtual uint16_t height() const = 0;
    virtual void pixel(int x, int y, uint16_t rgb565) = 0;
    virtual void present() = 0;
};

/* Stateless draw commands. Host has a full RGB565 backing store; target can
 * translate into batched ST7789 commands or a PSRAM framebuffer later.
 * Applications MUST NOT draw OS status/softkey surfaces in device integration.
 */
void fillRect(PixelSink& dst, int x, int y, int width, int height, uint16_t color);
void border(PixelSink& dst, int x, int y, int width, int height, uint16_t color);
bool sprite(PixelSink& dst, int x, int y, const Sprite565& image);
void smallText(PixelSink& dst, int x, int y, const char* text, uint16_t color, int scale=1);

class Platform : public PixelSink {
public:
    virtual void reservedSystemKey(KeyEvent event) = 0;
};

class App {
public:
    virtual ~App() = default;
    virtual void init(Platform& platform) = 0;
    virtual void update(uint32_t fixed_dt_ms) = 0;
    virtual void draw(Platform& platform) = 0;
    virtual void onKey(KeyEvent event) = 0;
    virtual void pause() = 0;
    virtual void resume() = 0;
    virtual void shutdown() = 0;
};

struct Config {
    uint16_t viewport_width = 240;
    uint16_t viewport_height = 320;
    uint32_t fixed_step_ms = 50;
    uint8_t max_catchup_steps = 4;
};
struct Stats {
    uint64_t updates=0;
    uint64_t renders=0;
    uint64_t dropped_ms=0;
    uint32_t input_overflows=0;
};
class Runtime final {
public:
    static constexpr size_t INPUT_CAPACITY=32;
    Runtime(App& app, Platform& platform, Config config={});
    bool start(uint32_t now_ms);
    bool queue(KeyEvent event);   // false if input buffer is full or OS-reserved
    void tick(uint32_t now_ms);  // monotonic millis; unsigned wrap is supported
    void pause();
    void resume(uint32_t now_ms);
    void stop();
    bool running() const {return started_;}
    bool paused() const {return paused_;}
    const Stats& stats() const {return stats_;}
private:
    void dispatch();
    App& app_;
    Platform& platform_;
    Config config_;
    Stats stats_{};
    KeyEvent queue_[INPUT_CAPACITY]{};
    size_t head_=0, size_=0;
    uint32_t last_ms_=0, accumulator_ms_=0;
    bool started_=false, paused_=false;
};
} // namespace qe
#endif
