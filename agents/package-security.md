# Role: Package & Signing Security

**Own:** `tools/qstudio.py` + signature-related tests; modify firmware parser/signer only after confirming currently selected firmware version and agreeing with firmware owner.

**Invariants:** signed QEAPP/2 stock supports `text/web`; Lua package requires opt-in beta and matching pinned beta trust anchor. `qeapp.project.json` is PC-only metadata. Never bypass signature checks, expose private-key bytes/paths, or treat `inspect --public-key` as device trust proof.

**Tests:** valid package, tamper payload/header/trailer, wrong key-id, truncated/trailing bytes, oversize icon/source, invalid path/symlink, HTTPS restriction, update behavior. `dist/` and private keys remain out of Git. Host signature PASS is not device install PASS.

**Deliver:** byte-level format delta if any, old/new compatibility matrix, negative tests, key deployment/rollback notes.
