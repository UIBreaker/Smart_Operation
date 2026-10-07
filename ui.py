"""
Smart Operation - Retro Hardware / Neumorphic Matte Edition
Thiết kế chủ đạo theo phong cách Vintage Cream Hardware (Braun / Dieter Rams / Teenage Engineering)
Bao gồm các khối: SLIDE (Điều khiển & Trạng thái), PRESS (Nút bấm 3D Matte), SCROLL (Bảng kịch bản)
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core import (
    enable_dpi_awareness,
    MacroAction,
    MacroManager,
    MacroStorage,
    play_sound,
)

# ==========================================
# RETRO HARDWARE COLOR PALETTE (From Reference Image)
# ==========================================
VINTAGE_BG = "#ece7de"             # Nền kem cổ điển tổng thể (Vintage Cream)
VINTAGE_CARD_BG = "#f6f3ec"        # Nền thẻ bề mặt mờ nhạt (Porcelain Matte)
VINTAGE_CARD_BORDER = "#ded7cb"    # Viền thẻ nổi nhẹ
VINTAGE_INNER_GROOVE = "#e4ded4"   # Rãnh thụt / khe trượt
VINTAGE_TEXT_HEAD = "#3e3a35"      # Chữ tiêu đề tối màu phong cách Dieter Rams
VINTAGE_TEXT_BODY = "#585249"      # Chữ thông tin chung
VINTAGE_TEXT_MUTED = "#8c8579"     # Chữ phụ / ghi chú

# Bảng màu nút 3D Matte (Phần "PRESS" trong ảnh tham khảo)
BTN_YELLOW_TOP = "#e8b056"
BTN_YELLOW_BOT = "#b88232"
BTN_YELLOW_TXT = "#433214"

BTN_GREEN_TOP = "#8eb77c"
BTN_GREEN_BOT = "#638c52"
BTN_GREEN_TXT = "#243a1c"

BTN_BLUE_TOP = "#96c5dc"
BTN_BLUE_BOT = "#699bb3"
BTN_BLUE_TXT = "#1c3848"

BTN_RED_TOP = "#d94f4f"
BTN_RED_BOT = "#a42a2a"
BTN_RED_TXT = "#ffffff"

BTN_BEIGE_TOP = "#e3ded4"
BTN_BEIGE_BOT = "#bcb5a7"
BTN_BEIGE_TXT = "#4d4841"

FONT_HEADER = ("Trebuchet MS", 13, "bold")
FONT_TITLE = ("Trebuchet MS", 10, "bold")
FONT_BODY = ("Segoe UI", 9)
FONT_BTN = ("Segoe UI", 9, "bold")


class Retro3DButton(tk.Canvas):
    """Nút bấm 3D bề mặt mờ (Matte) có hiệu ứng lún xuống khi nhấn (chính xác như ảnh tham khảo)."""
    def __init__(
        self,
        parent,
        text="",
        command=None,
        width=140,
        height=40,
        top_color=BTN_YELLOW_TOP,
        bot_color=BTN_YELLOW_BOT,
        text_color=BTN_YELLOW_TXT,
        font=FONT_BTN,
        radius=8,
        **kwargs
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent.cget("bg") if hasattr(parent, "cget") else VINTAGE_CARD_BG,
            highlightthickness=0,
            cursor="hand2",
            **kwargs
        )
        self.text = text
        self.command = command
        self.width = width
        self.height = height
        self.top_color = top_color
        self.bot_color = bot_color
        self.text_color = text_color
        self.font = font
        self.radius = radius
        self.pressed = False
        self.state = "normal"

        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self._draw()

    def _draw_round_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1 + r, y1, x2 - r, y1, x2, y1,
            x2, y1 + r, x2, y2 - r, x2, y2,
            x2 - r, y2, x1 + r, y2, x1, y2,
            x1, y2 - r, x1, y1 + r, x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)

    def _draw(self):
        self.delete("all")
        offset = 3 if self.pressed else 0
        w, h = self.width, self.height
        r = self.radius

        if self.state == "disabled":
            t_col = BTN_BEIGE_TOP
            b_col = BTN_BEIGE_BOT
            txt_col = VINTAGE_TEXT_MUTED
        else:
            t_col = self.top_color
            b_col = self.bot_color
            txt_col = self.text_color

        # Phần gờ đổ bóng 3D phía dưới (Bottom Bevel)
        self._draw_round_rect(2, 2, w - 2, h - 2, r, fill=b_col, outline="")
        # Bề mặt nút phía trên (Top Surface)
        self._draw_round_rect(2, 2 + offset, w - 2, h - 6 + offset, r, fill=t_col, outline="")
        # Chữ in chìm hoặc nổi
        self.create_text(
            w // 2,
            (h // 2 - 2) + offset,
            text=self.text,
            fill=txt_col,
            font=self.font,
        )

    def _on_press(self, event):
        if self.state == "disabled":
            return
        self.pressed = True
        self._draw()

    def _on_release(self, event):
        if self.state == "disabled":
            return
        self.pressed = False
        self._draw()
        if self.command:
            self.command()

    def configure_state(self, state: str):
        self.state = state
        self.configure(cursor="hand2" if state != "disabled" else "arrow")
        self._draw()

    def set_text(self, new_text: str):
        self.text = new_text
        self._draw()


class SmartOperationApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("SMART OPERATION // RETRO HARDWARE CONSOLE [v0.2.0]")
        self.root.geometry("880x750")
        self.root.minsize(820, 680)
        self.root.configure(bg=VINTAGE_BG)

        # Khởi tạo Core MacroManager
        self.manager = MacroManager()

        # Biến trạng thái
        self.speed_var = tk.StringVar(value="1.0x")
        self.loop_count_var = tk.StringVar(value="1")
        self.loop_delay_var = tk.StringVar(value="1.0")
        self.ignore_movement_var = tk.BooleanVar(value=True)  # Mặc định lọc bỏ chuột thừa
        self.countdown_var = tk.BooleanVar(value=True)

        self.countdown_timer = None
        self.current_file_path = None

        # Kết nối Callbacks
        self.manager.on_state_changed = self._on_manager_state_changed
        self.manager.on_action_recorded = self._on_action_recorded
        self.manager.on_step = self._on_player_step
        self.manager.on_play_finished = self._on_player_finished

        # Kích hoạt DPI Awareness
        enable_dpi_awareness()

        # Cài đặt Theme & Xây dựng Giao diện
        self._setup_retro_styles()
        self._build_ui()

        # Lắng nghe Hotkey toàn cầu (F8, F9, ESC)
        self.manager.start_global_hotkeys()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_retro_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Cấu hình Treeview phong cách thiết bị phần cứng kem cổ điển
        style.configure(
            "RetroHardware.Treeview",
            background="#faf8f3",
            foreground=VINTAGE_TEXT_HEAD,
            fieldbackground="#faf8f3",
            font=("Segoe UI", 9),
            rowheight=26,
            borderwidth=0,
        )
        style.configure(
            "RetroHardware.Treeview.Heading",
            background="#eae4d8",
            foreground=VINTAGE_TEXT_HEAD,
            font=("Trebuchet MS", 9, "bold"),
            relief=tk.FLAT,
        )
        style.map(
            "RetroHardware.Treeview",
            background=[("selected", BTN_BLUE_TOP)],
            foreground=[("selected", BTN_BLUE_TXT)],
        )

        style.configure(
            "RetroHardware.Vertical.TScrollbar",
            background=VINTAGE_CARD_BG,
            troughcolor=VINTAGE_INNER_GROOVE,
            arrowcolor=BTN_RED_TOP,
            borderwidth=0,
        )

    def _create_section_card(self, parent, section_name: str) -> tk.Frame:
        """Tạo một khối thẻ phần cứng kem bo viền có tiêu đề (SLIDE / PRESS / SCROLL)."""
        container = tk.Frame(parent, bg=VINTAGE_BG)
        container.pack(fill=tk.X, padx=16, pady=4)

        # Tiêu đề khối (Chữ in hoa phong cách retro công nghiệp)
        lbl_sec = tk.Label(
            container,
            text=section_name,
            font=FONT_HEADER,
            bg=VINTAGE_BG,
            fg=VINTAGE_TEXT_HEAD,
        )
        lbl_sec.pack(anchor="w", padx=4, pady=(2, 3))

        # Thẻ bo viền bề mặt mờ
        card = tk.Frame(
            container,
            bg=VINTAGE_CARD_BG,
            highlightbackground=VINTAGE_CARD_BORDER,
            highlightthickness=2,
            padx=14,
            pady=10,
        )
        card.pack(fill=tk.BOTH, expand=True)
        return card

    def _build_ui(self):
        # 0. MAIN HEADER (Tên ứng dụng)
        top_bar = tk.Frame(self.root, bg=VINTAGE_BG)
        top_bar.pack(fill=tk.X, padx=20, pady=(12, 4))

        tk.Label(
            top_bar,
            text="SMART OPERATION",
            font=("Trebuchet MS", 15, "bold"),
            bg=VINTAGE_BG,
            fg=VINTAGE_TEXT_HEAD,
        ).pack(side=tk.LEFT)

        tk.Label(
            top_bar,
            text="HIS AUTOMATION CONSOLE // v0.2.0",
            font=("Segoe UI", 9, "bold"),
            bg=VINTAGE_BG,
            fg=VINTAGE_TEXT_MUTED,
        ).pack(side=tk.RIGHT)

        # ==========================================
        # 1. KHỐI "SLIDE" (ĐIỀU KHIỂN & TRẠNG THÁI)
        # ==========================================
        slide_card = self._create_section_card(self.root, "SLIDE")

        # Rãnh hiển thị trạng thái (HUD Grooved Track)
        self.hud_track = tk.Frame(
            slide_card,
            bg=VINTAGE_INNER_GROOVE,
            highlightbackground=VINTAGE_CARD_BORDER,
            highlightthickness=1,
            padx=10,
            pady=6,
        )
        self.hud_track.pack(fill=tk.X, pady=(0, 8))

        self.hud_status_lbl = tk.Label(
            self.hud_track,
            text="● STATUS: SẴN SÀNG (READY)   │   [F8] HỌC THAO TÁC   │   [F9] CHẠY BOT   │   [ESC] DỪNG KHẨN CẤP",
            font=("Trebuchet MS", 9, "bold"),
            bg=VINTAGE_INNER_GROOVE,
            fg=BTN_GREEN_TXT,
        )
        self.hud_status_lbl.pack(anchor="center")

        # Rãnh thanh trượt cấu hình (Speed & Options)
        ctrl_row = tk.Frame(slide_card, bg=VINTAGE_CARD_BG)
        ctrl_row.pack(fill=tk.X)

        tk.Label(ctrl_row, text="TỐC ĐỘ PHÁT:", font=FONT_TITLE, bg=VINTAGE_CARD_BG, fg=VINTAGE_TEXT_HEAD).pack(side=tk.LEFT, padx=(0, 6))

        # Các nút bấm chọn tốc độ nhanh (Pill Buttons)
        self.speed_buttons = {}
        for spd_label in ["0.5x", "0.8x", "1.0x", "1.25x", "1.5x", "2.0x"]:
            is_default = (spd_label == "1.0x")
            btn = Retro3DButton(
                ctrl_row,
                text=spd_label,
                width=50,
                height=28,
                top_color=BTN_RED_TOP if is_default else BTN_BEIGE_TOP,
                bot_color=BTN_RED_BOT if is_default else BTN_BEIGE_BOT,
                text_color=BTN_RED_TXT if is_default else BTN_BEIGE_TXT,
                command=lambda s=spd_label: self._set_speed(s),
                radius=6,
            )
            btn.pack(side=tk.LEFT, padx=3)
            self.speed_buttons[spd_label] = btn

        # Số lần lặp
        tk.Label(ctrl_row, text="   LẶP:", font=FONT_TITLE, bg=VINTAGE_CARD_BG, fg=VINTAGE_TEXT_HEAD).pack(side=tk.LEFT, padx=(12, 4))
        self.entry_loop = tk.Entry(
            ctrl_row,
            textvariable=self.loop_count_var,
            width=4,
            bg=VINTAGE_INNER_GROOVE,
            fg=VINTAGE_TEXT_HEAD,
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
        )
        self.entry_loop.pack(side=tk.LEFT)

        # Nghỉ giữa vòng
        tk.Label(ctrl_row, text="   NGHỈ (s):", font=FONT_TITLE, bg=VINTAGE_CARD_BG, fg=VINTAGE_TEXT_HEAD).pack(side=tk.LEFT, padx=(8, 4))
        self.entry_delay = tk.Entry(
            ctrl_row,
            textvariable=self.loop_delay_var,
            width=4,
            bg=VINTAGE_INNER_GROOVE,
            fg=VINTAGE_TEXT_HEAD,
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT,
        )
        self.entry_delay.pack(side=tk.LEFT)

        # Checkboxes hàng dưới
        chk_row = tk.Frame(slide_card, bg=VINTAGE_CARD_BG)
        chk_row.pack(fill=tk.X, pady=(8, 0))

        tk.Checkbutton(
            chk_row,
            text="Bỏ qua di chuột thừa (Chỉ lưu Click & Phím - Tối ưu cho HIS)",
            variable=self.ignore_movement_var,
            font=FONT_BODY,
            bg=VINTAGE_CARD_BG,
            fg=VINTAGE_TEXT_BODY,
            activebackground=VINTAGE_CARD_BG,
            selectcolor=VINTAGE_INNER_GROOVE,
        ).pack(side=tk.LEFT, padx=(0, 16))

        tk.Checkbutton(
            chk_row,
            text="Đếm ngược 3 giây khi bắt đầu",
            variable=self.countdown_var,
            font=FONT_BODY,
            bg=VINTAGE_CARD_BG,
            fg=VINTAGE_TEXT_BODY,
            activebackground=VINTAGE_CARD_BG,
            selectcolor=VINTAGE_INNER_GROOVE,
        ).pack(side=tk.LEFT)

        # ==========================================
        # 2. KHỐI "PRESS" (HỆ NÚT BẤM 3D MATTE THEO ẢNH MẪU)
        # ==========================================
        press_card = self._create_section_card(self.root, "PRESS")

        # Hàng nút điều khiển chính (Row 1 trong ảnh)
        row1 = tk.Frame(press_card, bg=VINTAGE_CARD_BG)
        row1.pack(fill=tk.X, pady=(2, 6))

        self.btn_rec = Retro3DButton(
            row1,
            text="HỌC THAO TÁC (F8)",
            width=165,
            height=42,
            top_color=BTN_YELLOW_TOP,
            bot_color=BTN_YELLOW_BOT,
            text_color=BTN_YELLOW_TXT,
            command=self._cmd_start_recording,
        )
        self.btn_rec.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_play = Retro3DButton(
            row1,
            text="CHẠY THAO TÁC (F9)",
            width=165,
            height=42,
            top_color=BTN_GREEN_TOP,
            bot_color=BTN_GREEN_BOT,
            text_color=BTN_GREEN_TXT,
            command=self._cmd_start_playing,
        )
        self.btn_play.pack(side=tk.LEFT, padx=(0, 10))

        self.btn_stop = Retro3DButton(
            row1,
            text="DỪNG HỌC (F8)",
            width=140,
            height=42,
            top_color=BTN_BLUE_TOP,
            bot_color=BTN_BLUE_BOT,
            text_color=BTN_BLUE_TXT,
            command=self._cmd_stop_recording,
        )
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 10))
        self.btn_stop.configure_state("disabled")

        self.btn_panic = Retro3DButton(
            row1,
            text="DỪNG KHẨN CẤP (ESC)",
            width=180,
            height=42,
            top_color=BTN_RED_TOP,
            bot_color=BTN_RED_BOT,
            text_color=BTN_RED_TXT,
            command=self._cmd_emergency_stop,
        )
        self.btn_panic.pack(side=tk.RIGHT)

        # Hàng nút phụ quản lý kịch bản (Row 2 dạng nút con vuông/nhỏ trong ảnh)
        row2 = tk.Frame(press_card, bg=VINTAGE_CARD_BG)
        row2.pack(fill=tk.X, pady=(4, 2))

        Retro3DButton(row2, text="MỞ .JSON", width=95, height=34, top_color=BTN_BLUE_TOP, bot_color=BTN_BLUE_BOT, text_color=BTN_BLUE_TXT, command=self._cmd_load_file).pack(side=tk.LEFT, padx=(0, 6))
        Retro3DButton(row2, text="LƯU .JSON", width=95, height=34, top_color=BTN_YELLOW_TOP, bot_color=BTN_YELLOW_BOT, text_color=BTN_YELLOW_TXT, command=self._cmd_save_file).pack(side=tk.LEFT, padx=(0, 6))
        Retro3DButton(row2, text="SỬA ĐỘ TRỄ", width=105, height=34, top_color=BTN_GREEN_TOP, bot_color=BTN_GREEN_BOT, text_color=BTN_GREEN_TXT, command=self._cmd_edit_delay).pack(side=tk.LEFT, padx=(0, 6))
        Retro3DButton(row2, text="XÓA BƯỚC", width=95, height=34, top_color=BTN_BEIGE_TOP, bot_color=BTN_BEIGE_BOT, text_color=BTN_BEIGE_TXT, command=self._cmd_delete_selected_action).pack(side=tk.LEFT, padx=(0, 6))
        Retro3DButton(row2, text="XÓA HẾT", width=85, height=34, top_color=BTN_RED_TOP, bot_color=BTN_RED_BOT, text_color=BTN_RED_TXT, command=self._cmd_clear_actions).pack(side=tk.RIGHT)

        # ==========================================
        # 3. KHỐI "SCROLL" (BẢNG KỊCH BẢN THAO TÁC)
        # ==========================================
        scroll_card = self._create_section_card(self.root, "SCROLL")

        tree_frame = tk.Frame(scroll_card, bg=VINTAGE_CARD_BG)
        tree_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("stt", "delay", "type", "detail")
        self.tree = ttk.Treeview(
            tree_frame,
            columns=cols,
            show="headings",
            selectmode="browse",
            style="RetroHardware.Treeview",
            height=7,
        )

        self.tree.heading("stt", text="#")
        self.tree.heading("delay", text="CHỜ (s)")
        self.tree.heading("type", text="LOẠI THAO TÁC")
        self.tree.heading("detail", text="CHI TIẾT (TỌA ĐỘ / PHÍM BẤM)")

        self.tree.column("stt", width=45, anchor="center")
        self.tree.column("delay", width=85, anchor="center")
        self.tree.column("type", width=140, anchor="center")
        self.tree.column("detail", width=490, anchor="w")

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview, style="RetroHardware.Vertical.TScrollbar")
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Thống kê kịch bản ở đáy thẻ SCROLL
        stats_bar = tk.Frame(scroll_card, bg=VINTAGE_CARD_BG)
        stats_bar.pack(fill=tk.X, pady=(6, 0))

        self.lbl_stats = tk.Label(
            stats_bar,
            text="[ THAO TÁC: 000 ]   [ TỔNG THỜI GIAN: 0.0s ]",
            font=FONT_TITLE,
            bg=VINTAGE_CARD_BG,
            fg=VINTAGE_TEXT_HEAD,
        )
        self.lbl_stats.pack(side=tk.LEFT)

        tk.Label(
            stats_bar,
            text="💡 Gợi ý HIS: Sửa độ trễ trước bước Ký số lên 1.5s - 2.0s để máy chủ kịp nạp chứng thư số.",
            font=("Segoe UI", 8, "italic"),
            bg=VINTAGE_CARD_BG,
            fg=VINTAGE_TEXT_MUTED,
        ).pack(side=tk.RIGHT)

    # ==========================================
    # LOGIC ĐIỀU KHIỂN & CẬP NHẬT TRẠNG THÁI
    # ==========================================
    def _set_speed(self, spd_text: str):
        self.speed_var.set(spd_text)
        for k, btn in self.speed_buttons.items():
            is_active = (k == spd_text)
            btn.top_color = BTN_RED_TOP if is_active else BTN_BEIGE_TOP
            btn.bot_color = BTN_RED_BOT if is_active else BTN_BEIGE_BOT
            btn.text_color = BTN_RED_TXT if is_active else BTN_BEIGE_TXT
            btn._draw()

    def _parse_speed(self) -> float:
        raw = self.speed_var.get()
        try:
            return float(raw.replace("x", "").strip())
        except Exception:
            return 1.0

    def _parse_loop_count(self) -> int:
        try:
            return max(0, int(self.loop_count_var.get().strip()))
        except Exception:
            return 1

    def _parse_loop_delay(self) -> float:
        try:
            return max(0.0, float(self.loop_delay_var.get().strip()))
        except Exception:
            return 1.0

    def _cmd_start_recording(self):
        if self.countdown_var.get():
            self._start_countdown(3)
        else:
            self._do_start_record()

    def _start_countdown(self, seconds_left: int):
        if seconds_left > 0:
            self._set_hud(
                f"⏳ CHUẨN BỊ GHI TRONG 0{seconds_left} GIÂY... HÃY CHUYỂN SANG MÀN HÌNH HIS NGAY!",
                fg=BTN_RED_BOT,
            )
            play_sound("start_play")
            self.countdown_timer = self.root.after(1000, lambda: self._start_countdown(seconds_left - 1))
        else:
            self._do_start_record()

    def _do_start_record(self):
        record_movement = not self.ignore_movement_var.get()
        self._clear_tree()
        self.manager.start_recording(record_movement=record_movement)

    def _cmd_stop_recording(self):
        if self.countdown_timer:
            self.root.after_cancel(self.countdown_timer)
            self.countdown_timer = None
        self.manager.stop_recording()

    def _cmd_start_playing(self):
        if not self.manager.actions:
            messagebox.showwarning("THÔNG BÁO", "Chưa có thao tác nào trong kịch bản!\nNhấn F8 để học thao tác hoặc mở file .json đã lưu.")
            return
        speed = self._parse_speed()
        loops = self._parse_loop_count()
        delay = self._parse_loop_delay()
        self.manager.start_playing(speed=speed, loop_count=loops, loop_delay=delay)

    def _cmd_emergency_stop(self):
        if self.countdown_timer:
            self.root.after_cancel(self.countdown_timer)
            self.countdown_timer = None
        if self.manager.state == MacroManager.STATE_RECORDING:
            self.manager.stop_recording()
        elif self.manager.state == MacroManager.STATE_PLAYING:
            self.manager.stop_playing()

    def _set_hud(self, text: str, fg: str):
        self.hud_status_lbl.configure(text=text, fg=fg)

    def _on_manager_state_changed(self, new_state: str):
        self.root.after(0, lambda: self._handle_state_ui(new_state))

    def _handle_state_ui(self, state: str):
        if state == MacroManager.STATE_IDLE:
            self._set_hud(
                "● STATUS: SẴN SÀNG (READY)   │   [F8] HỌC THAO TÁC   │   [F9] CHẠY BOT   │   [ESC] DỪNG KHẨN CẤP",
                fg=BTN_GREEN_TXT,
            )
            self.btn_rec.configure_state("normal")
            self.btn_stop.configure_state("disabled")
            self.btn_play.configure_state("normal")
            self._refresh_action_tree()

        elif state == MacroManager.STATE_RECORDING:
            self._set_hud(
                "🔴 [REC] ĐANG GHI NHỚ THAO TÁC... HÃY LÀM TRÊN HIS! XONG NHẤN F8 HOẶC ESC ĐỂ LƯU",
                fg=BTN_RED_BOT,
            )
            self.btn_rec.configure_state("disabled")
            self.btn_stop.configure_state("normal")
            self.btn_play.configure_state("disabled")

        elif state == MacroManager.STATE_PLAYING:
            self._set_hud(
                "🔵 [RUN] BOT ĐANG TỰ ĐỘNG THỰC THI... NHẤN PHÍM ESC BẤT CỨ LÚC NÀO ĐỂ DỪNG NGAY!",
                fg=BTN_BLUE_TXT,
            )
            self.btn_rec.configure_state("disabled")
            self.btn_stop.configure_state("disabled")
            self.btn_play.configure_state("disabled")

    def _on_action_recorded(self, action: MacroAction, count: int):
        self.root.after(0, lambda: self._add_action_to_tree(action, count))

    def _on_player_step(self, step: int, total: int, cur_loop: int, total_loops: int):
        loop_str = f"VÒNG {cur_loop}/{total_loops}" if total_loops > 0 else f"VÒNG {cur_loop} (VÔ HẠN)"
        txt = f"🔵 [RUN] {loop_str} ── BƯỚC {step:02d}/{total:02d} │ NHẤN ESC ĐỂ DỪNG KHẨN CẤP"
        self.root.after(0, lambda: self._set_hud(txt, fg=BTN_BLUE_TXT))

    def _on_player_finished(self, success: bool, aborted: bool):
        if aborted:
            msg = "ĐÃ DỪNG KHẨN CẤP THEO LỆNH (ESC)"
            self.root.after(0, lambda: self._set_hud(f"⚠️ {msg} │ [F8] GHI TIẾP │ [F9] CHẠY LẠI", fg=BTN_YELLOW_TXT))
        else:
            msg = "HOÀN TẤT TOÀN BỘ KỊCH BẢN THÀNH CÔNG!"
            self.root.after(0, lambda: self._set_hud(f"⭐ {msg} │ [F8] GHI TIẾP │ [F9] CHẠY LẠI", fg=BTN_GREEN_TXT))

    # ==========================================
    # QUẢN LÝ BẢNG KỊCH BẢN (TREEVIEW)
    # ==========================================
    def _format_action_display(self, action: MacroAction):
        act_type = action.action_type
        if act_type == "mouse_click":
            st = "Nhấn" if action.pressed else "Nhả"
            btn = (action.button or "left").upper()
            t_name = f"Chuột {btn} ({st})"
            detail = f"Tọa độ: X={action.x}, Y={action.y}"
        elif act_type == "mouse_move":
            t_name = "Di chuột"
            detail = f"Tọa độ: X={action.x}, Y={action.y}"
        elif act_type == "mouse_scroll":
            t_name = "Cuộn chuột"
            detail = f"Tại ({action.x}, {action.y}) | Cuộn: {action.dy}"
        elif act_type == "key_press":
            t_name = "Nhấn phím"
            detail = f"Phím: [{action.key}]"
        elif act_type == "key_release":
            t_name = "Nhả phím"
            detail = f"Phím: [{action.key}]"
        else:
            t_name = act_type.upper()
            detail = str(action.to_dict())

        delay_str = f"{action.delay:.3f}s"
        return t_name, detail, delay_str

    def _add_action_to_tree(self, action: MacroAction, stt: int):
        t_name, detail, delay_str = self._format_action_display(action)
        item_id = self.tree.insert("", tk.END, values=(f"{stt:02d}", delay_str, t_name, detail))
        self.tree.see(item_id)
        self._update_stats()

    def _clear_tree(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._update_stats()

    def _refresh_action_tree(self):
        self._clear_tree()
        for idx, act in enumerate(self.manager.actions, start=1):
            t_name, detail, delay_str = self._format_action_display(act)
            self.tree.insert("", tk.END, values=(f"{idx:02d}", delay_str, t_name, detail))
        self._update_stats()

    def _update_stats(self):
        total = len(self.manager.actions)
        total_time = sum(act.delay for act in self.manager.actions)
        self.lbl_stats.configure(text=f"[ THAO TÁC: {total:03d} ]   [ TỔNG THỜI GIAN: {total_time:.2f}s ]")

    def _cmd_delete_selected_action(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("THÔNG BÁO", "Hãy chọn một dòng trong bảng để xóa!")
            return
        idx = self.tree.index(selected[0])
        if 0 <= idx < len(self.manager.actions):
            del self.manager.actions[idx]
            self._refresh_action_tree()

    def _cmd_edit_delay(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("THÔNG BÁO", "Hãy chọn một dòng trong bảng để sửa thời gian chờ!")
            return
        idx = self.tree.index(selected[0])
        action = self.manager.actions[idx]

        new_val = simpledialog.askfloat(
            "SỬA ĐỘ TRỄ",
            f"Nhập thời gian chờ trước bước #{idx + 1} (giây):",
            initialvalue=action.delay,
            minvalue=0.0,
            maxvalue=300.0,
        )
        if new_val is not None:
            action.delay = round(new_val, 4)
            self._refresh_action_tree()

    def _cmd_clear_actions(self):
        if not self.manager.actions:
            return
        if messagebox.askyesno("XÁC NHẬN", "Bạn có chắc chắn muốn xóa toàn bộ kịch bản hiện tại?"):
            self.manager.actions = []
            self._refresh_action_tree()

    # ==========================================
    # LƯU & MỞ FILE KỊCH BẢN (.JSON)
    # ==========================================
    def _cmd_save_file(self):
        if not self.manager.actions:
            messagebox.showwarning("CẢNH BÁO", "Không có thao tác nào để lưu!")
            return

        file_path = filedialog.asksaveasfilename(
            title="LƯU KỊCH BẢN THAO TÁC",
            defaultextension=".json",
            filetypes=[("JSON Macro Script", "*.json"), ("All Files", "*.*")],
            initialfile="his_ki_so_ket_thuc.json",
        )
        if not file_path:
            return

        try:
            MacroStorage.save_to_file(
                self.manager.actions,
                file_path,
                metadata={
                    "speed": self.speed_var.get(),
                    "loop_count": self.loop_count_var.get(),
                },
            )
            self.current_file_path = file_path
            messagebox.showinfo("THÀNH CÔNG", f"Đã lưu kịch bản vào file:\n{os.path.basename(file_path)}")
        except Exception as ex:
            messagebox.showerror("LỖI KHI LƯU", str(ex))

    def _cmd_load_file(self):
        file_path = filedialog.askopenfilename(
            title="MỞ KỊCH BẢN THAO TÁC",
            filetypes=[("JSON Macro Script", "*.json"), ("All Files", "*.*")],
        )
        if not file_path:
            return

        try:
            actions = MacroStorage.load_from_file(file_path)
            self.manager.actions = actions
            self.current_file_path = file_path
            self._refresh_action_tree()
            messagebox.showinfo("THÀNH CÔNG", f"Đã nạp {len(actions)} thao tác từ:\n{os.path.basename(file_path)}")
        except Exception as ex:
            messagebox.showerror("LỖI KHI MỞ", str(ex))

    def _on_close(self):
        self.manager.stop_global_hotkeys()
        self.manager.stop_playing()
        if self.countdown_timer:
            self.root.after_cancel(self.countdown_timer)
        self.root.destroy()


def run_app():
    root = tk.Tk()
    app = SmartOperationApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_app()
