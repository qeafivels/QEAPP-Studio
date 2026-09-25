/* QEAPP Studio engine C ABI IDEA, v0.1 - NOT included in VQEAF OS v2.4.2.
 * Do NOT compile into production without a versioned package spec, sandbox
 * implementation and device verification. This header models host/ESP32 seam.
 */
#ifndef QEAPP_ENGINE_API_DRAFT_H
#define QEAPP_ENGINE_API_DRAFT_H
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif

enum { QE_ENGINE_API_DRAFT_V1 = 0x00010000 };
typedef enum {
    QE_KEY_UP, QE_KEY_DOWN, QE_KEY_LEFT, QE_KEY_RIGHT,
    QE_KEY_OK, QE_KEY_BACK, QE_KEY_DELETE, QE_KEY_OPTION
} QeKeyDraft;
typedef struct {
    uint32_t api_version;
    uint32_t (*ticks_ms)(void *user);
    void (*put_pixel_clipped)(void *user, int16_t x, int16_t y, uint16_t rgb565);
    int (*load_slot)(void *user, unsigned slot, uint8_t *dst, uint32_t capacity);
    int (*save_slot)(void *user, unsigned slot, const uint8_t *src, uint32_t len);
    void *user;
} QePlatformDraft;
typedef struct {
    uint32_t max_script_bytes;
    uint32_t max_heap_bytes;
    uint32_t max_instructions_per_tick;
} QeRuntimeBudgetDraft;
/* MENU/Home and SELECT long-press are reserved for OS, never forwarded as user code. */
#ifdef __cplusplus
}
#endif
#endif
