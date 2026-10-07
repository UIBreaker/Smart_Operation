# 🎛️ Smart Operation // [Vintage Hardware Edition]

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-lightgrey.svg)](https://www.microsoft.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Style](https://img.shields.io/badge/style-Vintage%20Matte%20Cream-d9534f.svg)](#)


## ⚡ Tính Năng Cốt Lõi

1. **Học thao tác thông minh (Smart Learn)**:
   - Ghi lại các cú click chuột (trái, phải, đúp), phím bấm (text, Tab, Enter, Ctrl,...).
   - **Tối ưu cho HIS**: Tự động lọc bỏ các di chuyển chuột thừa (mouse movement jitter), chỉ giữ lại điểm click và phím gõ chính xác, giúp kịch bản chạy dứt khoát và mượt mà.
   - **Chuẩn 100% DPI Scaling**: Tích hợp Windows Per-monitor DPI Awareness, không bao giờ bị click lệch tọa độ trên màn hình 125% hay 150%.
2. **Phím tắt toàn cục (Global Hotkeys)**:
   - `[F8]`: Bắt đầu / Dừng học thao tác (nhấn trực tiếp từ màn hình HIS).
   - `[F9]`: Chạy kịch bản tự động.
   - `[ESC]`: **Dừng khẩn cấp ngay lập tức (Panic Stop)** — nhả toàn bộ phím/chuột và ngắt luồng dưới 50ms.
3. **Quản lý kịch bản linh hoạt**:
   - Tùy chỉnh tốc độ: `0.5x`, `0.8x (An toàn)`, `1.0x (Chuẩn)`, `1.25x`, `1.5x`, `2.0x`.
   - Thiết lập số lần lặp và thời gian nghỉ giữa các vòng.
   - Cho phép chỉnh sửa thời gian chờ (delay) hoặc xóa bước thừa trực tiếp trên bảng.
   - Lưu & Nạp kịch bản dạng file `.json` dùng lại lâu dài hoặc chia sẻ cho đồng nghiệp.

---

## 🚀 Hướng Dẫn Cài Đặt & Sử Dụng

### 1. Tải về máy
Clone repository về máy tính:
```bash
git clone https://github.com/UIBreaker/Smart_Operation.git
cd Smart_Operation
```
Hoặc tải file thực thi đóng gói sẵn từ mục [Releases](https://github.com/UIBreaker/Smart_Operation/releases).

### 2. Cài đặt thư viện
Yêu cầu Python 3.8 trở lên:
```bash
pip install -r requirements.txt
```

### 3. Khởi chạy
- **Cách 1 (Nhanh nhất)**: Nhấp đúp chuột vào file **`run.bat`**.
- **Cách 2**: Chạy từ dòng lệnh:
  ```bash
  python main.py
  ```

---



## 📄 Bản Quyền (License)
Dự án được phân phối dưới giấy phép **MIT License**.
