# Role: VQEAF OS Core & Device

**Own:** user-approved current VQEAF OS checkout only. Studio's bundled firmware is a reference snapshot that may be older than Back r2.

**Visual freeze:** for core-only Back requests, record hash baseline and leave every icon, theme, font, pixel atlas, layout and renderer file unchanged. Reuse existing OS notification widget. MENU/Home, A/Back and B/Delete remain distinct. No hypothetical Nokia/S40 theme changes.

**Key Back cases:** app → confirm; No → resume exact app state; Yes → shut down app then launcher; double Back no duplicate dialog; timer/overlay cannot paint over popup; audio owner/resource cleanup correct on exit; installer busy → cancel confirmation without partial package. Avoid blocking task in ISR/input loop.

**Gate tiers:** host/unit regressions → PlatformIO build (matching board env) → physical-device Serial 115200, LCD video, 20+ Back cycles, FPS/heap/PSRAM and speaker SFX when available. `pio run` is compile, not proof of UI/audio quality. Do not speculate about reset reason from missing logs.

**Deliver:** touched core files + SHA-256 unchanged visual set, test summary and explicit device verification state.
