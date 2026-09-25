# QEAPP-Studio AI Agent Kit v1.1 — Changelog

**Loại phát hành:** tài liệu và công cụ kiểm tra, trên nền Studio v0.7.4. **Không cập nhật** IDE runtime, Lua VM, firmware, launcher, GPIO, renderer, Retro-Go assets, package contract hoặc trust key.

- `AGENTS.md`: thay entry-point ngắn bằng hợp đồng điều phối, scope/owner/QA, vùng tệp nóng, 7 giai đoạn và điều kiện chặn release.
- `agents/orchestrator.md`: trách nhiệm, quy trình giao việc và trạng thái giao nhận có thể audit.
- `docs/agents/TASK_BRIEF_TEMPLATE.md`: mẫu đầu vào mỗi task để khóa baseline, allow-list và gate trước khi sửa.
- `docs/agents/HANDOFF_TEMPLATE.md`: mẫu bàn giao chi tiết, hỗ trợ test evidence, reviewer, rollback và mô tả commit `Why/What/Tests/Limits`.
- `docs/agents/TEST_MATRIX.md`: kiểm thử theo 5 tier, ID ổn định, điều kiện PASS và bằng chứng tối thiểu; ngăn nhầm lẫn host với device.
- `agents/qa-release.md`, `docs/agents/README.md`, `README_INSTALL.md`: cập nhật workflow và link.
- `tools/validate_agent_docs.py`, `tools/test_agent_docs.py`, `DOCS_MANIFEST.json`: bổ sung kiểm tra liên kết/manifest và kiểm thử logic mẫu.

**Cần kiểm thử:** `python tools/validate_agent_docs.py` và `python -m unittest discover -s tools -p test_agent_docs.py -v`. Không dùng kết quả này để khẳng định Windows GUI hoặc ESP32-S3.
