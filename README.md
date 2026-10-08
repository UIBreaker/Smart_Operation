# 🎛️ Smart Operation // [v0.10.2 Script Management Edition]

> **Trợ Lý Tự Động Hóa Thao Tác Máy Tính & Phần Mềm Y Tế (HIS)**  
> **Tác giả:** Nhật Nam ([@UIBreaker](https://github.com/UIBreaker))

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-lightgrey.svg)](https://www.microsoft.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Release](https://img.shields.io/badge/release-v0.10.2-success.svg)](https://github.com/UIBreaker/Smart_Operation/releases/tag/v0.10.2)
[![Author](https://img.shields.io/badge/author-Nh%E1%BA%ADt%20Nam%20%28%40UIBreaker%29-orange.svg)](https://github.com/UIBreaker)

---

## 🌟 Điểm Mới Nổi Bật Ở Phiên Bản v0.10.2

1. **🗑️ Tính Năng Xóa Kịch Bản Linh Hoạt (Delete Profile)**:
   - Dễ dàng xóa kịch bản không còn sử dụng:
     - Bấm nút **`[🗑️ XÓA]`** màu đỏ trên thanh công cụ Script Deck để xóa kịch bản đang chọn.
     - Hoặc bấm nút biểu tượng **`🗑️`** nhỏ trực tiếp trên từng thẻ kịch bản.
   - Hộp thoại xác nhận an toàn trước khi xóa, tránh thao tác nhầm lẫn.
   - Cơ chế bảo vệ tự động: luôn đảm bảo giữ lại ít nhất 1 kịch bản trong thư viện.
   - Bắn thông báo Windows Toast xác nhận ngay sau khi xóa.

2. **🔔 Thông Báo Windows Toast Toàn Diện**:
   - Hiện thông báo trực tiếp ở góc dưới màn hình Windows khi:
     - 🔴 Bắt đầu học thao tác
     - ⏹ Dừng học & lưu thao tác
     - 🛑 Dừng khẩn cấp (Panic Stop)
     - 🗑 Xóa sạch các bước / Xóa kịch bản
     - ▶ Bắt đầu chạy kịch bản
     - ⭐ Hoàn thành kịch bản

3. **📋 Sao Chép & Dán Kịch Bản Giữa Các Máy Tính**:
   - **Nút `[📋 SAO CHÉP MÃ]`**: Copy toàn bộ kịch bản vào bộ nhớ tạm chỉ với 1 cú click để gửi qua Zalo / Messenger / Email.
   - **Nút `[📥 DÁN KỊCH BẢN]`**: Ở máy tính khác, bấm nút này là tự động nạp kịch bản vào và chạy được ngay, không cần cấu hình lại!

4. **📁 Bố Cục Danh Sách Kịch Bản Trực Quan**:
   - Các kịch bản được sắp xếp dạng thẻ (Deck Cards) hiển thị rõ tên kịch bản, phím tắt gán (`[F9]`, `[F10]`,...) và số bước thực hiện.

5. **🔕 Chạy Ngầm Khay Hệ Thống (System Tray)**:
   - Thu nhỏ xuống khay đồng hồ Windows khi bấm `[X]` hoặc `[🔻 THU VÀO KHAY]`. Phím tắt vẫn hoạt động 100% trong nền.

6. **⚙️ Tùy Biến Phím Tắt Trong Cài Đặt**:
   - Tùy chỉnh phím Học thao tác (mặc định: `F8`) và phím Dừng khẩn cấp (mặc định: `ESC`).

---

## 🚀 Hướng Dẫn Cài Đặt & Sử Dụng

### 1. Tải về file chạy sẵn (Khuyên dùng)
Tải bản cài đặt đóng gói sẵn từ mục [Releases v0.10.2](https://github.com/UIBreaker/Smart_Operation/releases/tag/v0.10.2):
- **`SmartOperation.exe`**: Tải về nhấp đúp là chạy ngay (không cần cài Python).
- **`SmartOperation-v0.10.2-Windows.zip`**: Gói nén đầy đủ.

### 2. Chạy từ mã nguồn Python
```bash
git clone https://github.com/UIBreaker/Smart_Operation.git
cd Smart_Operation
pip install -r requirements.txt
python main.py
```

---

## 👤 Thông Tin Tác Giả & Bản Quyền
- **Tác giả:** Nhật Nam
- **GitHub:** [@UIBreaker](https://github.com/UIBreaker)
- **Giấy phép:** [MIT License](LICENSE)
