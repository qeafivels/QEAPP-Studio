# QEAPP Studio sample applications

- [Pocket Focus](pocket-focus/README_VN.md): interactive host Lua focus timer with replay tests; includes stock-firmware text guide sample.
- [Pocket Calculator](pocket-calculator/README_VN.md): interactive host Lua calculator with keyboard tests; includes stock-firmware text guide sample.

For interactive preview, open the `projects/*-lua` subproject using Studio's Virtual Phone. Only `*-guide` text packages are supported on the default shipping firmware; installing a Lua app requires experimental Lua beta firmware. Run `tests/verify_sample.py --studio ../.. --system-lua` only on a development host with a compatible firmware checkout and the system Lua diagnostics available. Real ESP32-S3 testing is a separate gate.
