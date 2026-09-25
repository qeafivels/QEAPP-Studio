# Pixel Snake — C++ HOST sample

Dùng `../../tools/qstudio.py simulate --demo snake --scenario playing -o screenshot.png` từ thư mục root bộ kit. Game 16x18, logical canvas 240x320, fixed step 50ms, input từ replay hoặc qe::Runtime C++.

Không nên sao chép trực tiếp thành `.qeapp` QEAPP/2: firmware v2.4.2 chưa có bộ nạp C++ plugin hoặc Lua, `.qeapp` chỉ hỗ trợ signed text/web với Snake C++ nhúng sẵn như một ngoại lệ khác.
