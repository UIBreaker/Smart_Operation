# 🎛️ Smart Operation // [Vintage Hardware Edition]

> **Trợ Lý Tự Động Hóa Thao Tác Máy Tính & Phần Mềm Y Tế (HIS) - Phong cách Thiết Kế Phần Cứng Cổ Điển (Vintage Cream / Dieter Rams / Neumorphic Matte)**

[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%20%7C%2011-lightgrey.svg)](https://www.microsoft.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Style](https://img.shields.io/badge/style-Vintage%20Matte%20Cream-d9534f.svg)](#)

**Smart Operation** là công cụ tự động hóa thao tác (Macro / Robotic Process Automation) siêu nhẹ dành cho Windows, được thiết kế đặc biệt để giải quyết các quy trình lặp đi lặp lại hàng ngày trên các phần mềm quản lý bệnh viện (**HIS**), phòng khám và ứng dụng văn phòng:
- 🩺 **Điền form bệnh án & kết luận chuẩn**
- ✍️ **Ký số điện tử (USB Token / Cloud CA)**
- 🏁 **Kết thúc ca khám & in đơn thuốc**

---

## 🎨 Điểm Nhấn Thiết Kế [Vintage Hardware Console]

Lấy cảm hứng từ ngôn ngữ thiết kế thiết bị âm thanh Hi-Fi và máy chơi game cổ điển của Braun, Dieter Rams và Teenage Engineering:

```
┌──────────────────────────────────────────────────────────────┐
│  SLIDE   [ Thanh trượt tốc độ & Biển báo trạng thái HUD ]    │
│  PRESS   [ Hệ nút bấm 3D Matte: Vàng, Xanh Lá, Xanh Dương ] │
│  SCROLL  [ Bảng kịch bản thao tác & Rãnh cuộn console ]      │
└──────────────────────────────────────────────────────────────┘
```

1. **SLIDE**: 
   - Rãnh trượt trạng thái thời gian thực với đèn báo LED.
   - Các nút chọn tốc độ dạng phím gạt: `0.5x`, `0.8x`, `1.0x (CHUẨN)`, `1.25x`, `1.5x`, `2.0x`.
2. **PRESS**:
   - Các nút bấm khối 3D bề mặt mờ (Matte Finish) phản hồi cơ học: Khi nhấp chuột, nút sẽ **lún xuống** và nảy lên chân thực.
   - Bảng màu hoài cổ sang trọng: Vàng Mustard (`#e8b056`), Xanh Matcha (`#8eb77c`), Xanh Baby Blue (`#96c5dc`) và Đỏ Coral (`#d94f4f`).
3. **SCROLL**:
   - Bảng kịch bản hiển thị trên nền kem sứ mờ (`#faf8f3`), font chữ đậm nét, dễ quan sát từ xa trong phòng khám.

---

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

## 🩺 Hướng Dẫn Quy Trình Thực Tế Cho Phần Mềm HIS

Giả sử quy trình khám của bạn gồm: **Điền kết luận -> Bấm Ký số -> Chờ cửa sổ ký xác nhận -> Bấm Kết thúc khám**:

### Bước 1: Học quy trình (Chỉ làm 1 lần)
1. Mở phần mềm HIS và phần mềm **Smart Operation**.
2. Chuyển sang màn hình ca khám trên phần mềm HIS.
3. Nhấn phím **`[F8]`** trên bàn phím (nghe tiếng "bíp" bắt đầu ghi).
4. Thực hiện các thao tác:
   - Bấm vào ô chẩn đoán -> Nhập kết luận mẫu.
   - Bấm vào nút **Ký số**.
   - Chờ bảng USB Token hiện lên -> Bấm nút **Xác nhận / Ký**.
   - Bấm nút **Kết thúc khám**.
5. Nhấn lại phím **`[F8]`** (hoặc **`[ESC]`**). Nghe tiếng bíp báo hiệu hoàn tất.

### Bước 2: Tinh chỉnh thời gian chờ
1. Quay lại Smart Operation, kiểm tra danh sách các bước đã ghi trong khối **SCROLL**.
2. Tại bước click nút **Ký số**, do USB Token hoặc máy chủ HIS thường mất khoảng 1.5 - 2 giây để nạp chữ ký, bạn chọn dòng đó và bấm **`SỬA ĐỘ TRỄ`**, nhập `1.5` hoặc `2.0` (giây).
3. Bấm **`LƯU .JSON`** để lưu kịch bản (ví dụ: `his_ki_so_ket_thuc.json`).

### Bước 3: Sử dụng cho các bệnh nhân tiếp theo
1. Mỗi khi chuyển sang ca khám của bệnh nhân mới trên HIS:
2. Chỉ cần nhấn phím **`[F9]`**!
3. Bot sẽ tự động thực hiện toàn bộ quy trình điền, ký số và kết thúc khám.
4. **Nếu có bất kỳ sự cố nào**: Nhấn ngay phím **`[ESC]`** để dừng bot ngay lập tức.

---

## 📦 Đóng Gói Thành File `.exe` Độc Lập

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile --name "SmartOperation" main.py
```
File thực thi nằm tại: `dist/SmartOperation.exe`.

---

## 📄 Bản Quyền (License)
Dự án được phân phối dưới giấy phép **MIT License**.
