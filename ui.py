"""
Smart Operation - Retro Hardware / Neumorphic Matte Edition (v0.4.1)
Tính năng mới v0.4.1:
- Chạy ngầm dưới Khay hệ thống Windows (System Tray / Notification Area), phím tắt hoạt động 100% khi ẩn.
- Quản lý đa kịch bản (Multi-Script Profiles): Mỗi kịch bản có tên riêng và tổ hợp phím kích hoạt riêng (F9, F10, F11, Ctrl+F1,...).
- Bảng Cài đặt tổ hợp phím (Hotkey Settings) cho phím Học, phím Dừng khẩn cấp và thu nhỏ xuống khay.
- Giữ trọn ngôn ngữ thiết kế Vintage Cream Hardware (SLIDE - PRESS - SCROLL).
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from PIL import Image, ImageDraw
import pystray

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from core import (
    enable_dpi_awareness,
    MacroAction,
    ScriptProfile,
    MacroManager,
    MacroStorage,
    normalize_hotkey,
    play_sound,
)

# ==========================================
# RETRO HARDWARE COLOR PALETTE (Braun / Dieter Rams)
# ==========================================
VINTAGE_BG = "#ece7de"             # Nền kem cổ điển tổng thể
VINTAGE_CARD_BG = "#f6f3ec"        # Nền thẻ bề mặt mờ nhạt
VINTAGE_CARD_BORDER = "#ded7cb"    # Viền thẻ nổi nhẹ
VINTAGE_INNER_GROOVE = "#e4ded4"   # Rãnh thụt / khe trượt
VINTAGE_TEXT_HEAD = "#3e3a35"      # Chữ tiêu đề tối màu
VINTAGE_TEXT_BODY = "#585249"      # Chữ thông tin chung
VINTAGE_TEXT_MUTED = "#8c8579"     # Chữ phụ / ghi chú

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

FONT_HEADER = ("Trebuchet MS", 12, "bold")
FONT_TITLE = ("Trebuchet MS", 9, "bold")
FONT_BODY = ("Segoe UI", 9)
FONT_BTN = ("Segoe UI", 9, "bold")


def create_tray_icon_image():
    """Tạo biểu tượng System Tray phong cách Vintage Hardware (64x64 RGBA)."""
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    # Vòng tròn ngoài kem
    draw.ellipse([4, 4, 60, 60], fill="#ece7de", outline="#ded7cb", width=3)
    # Nút bấm đỏ bên trong
    draw.ellipse([14, 14, 50, 50], fill="#d94f4f", outline="#a42a2a", width=2)
    # Chấm trắng điểm nhấn
    draw.ellipse([26, 26, 38, 38], fill="#ffffff")
    return img


class Retro3DButton(tk.Canvas):
    """Nút bấm 3D bề mặt mờ (Matte) có độ nảy cơ học khi nhấp."""
    def __init__(
        self,
        parent,
        text="",
        command=None,
        width=130,
        height=38,
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

        self._draw_round_rect(2, 2, w - 2, h - 2, r, fill=b_col, outline="")
        self._draw_round_rect(2, 2 + offset, w - 2, h - 6 + offset, r, fill=t_col, outline="")
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
        self.root.title("SMART OPERATION // RETRO HARDWARE CONSOLE [v0.4.1]")
        self.root.geometry("900x780")
        self.root.minsize(840, 700)
        self.root.configure(bg=VINTAGE_BG)

        # Khởi tạo Core MacroManager
        self.manager = MacroManager()

        # Biến cấu hình giao diện
        self.speed_var = tk.StringVar(value="1.0x")
        self.loop_count_var = tk.StringVar(value="1")
        self.loop_delay_var = tk.StringVar(value="1.0")
        self.ignore_movement_var = tk.BooleanVar(value=True)
        self.countdown_var = tk.BooleanVar(value=True)

        self.countdown_timer = None
        self.tray_icon: Optional[pystray.Icon] = None

        # Kết nối Callbacks từ Core Manager
        self.manager.on_state_changed = self._on_manager_state_changed
        self.manager.on_action_recorded = self._on_action_recorded
        self.manager.on_step = self._on_player_step
        self.manager.on_play_finished = self._on_player_finished
        self.manager.on_profile_triggered = self._on_profile_triggered

        # Kích hoạt DPI Awareness
        enable_dpi_awareness()

        # Cài đặt Theme & Xây dựng Giao diện
        self._setup_retro_styles()
        self._build_ui()

        # Khởi động phím tắt toàn cục
        self.manager.start_global_hotkeys()

        # Khởi động Khay hệ thống (System Tray)
        self._setup_system_tray()

        # Bắt sự kiện đóng cửa sổ
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)

    def _setup_retro_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

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
        container = tk.Frame(parent, bg=VINTAGE_BG)
        container.pack(fill=tk.X, padx=16, pady=3)

        lbl_sec = tk.Label(
            container,
            text=section_name,
            font=FONT_HEADER,
            bg=VINTAGE_BG,
            fg=VINTAGE_TEXT_HEAD,
        )
        lbl_sec.pack(anchor="w", padx=4, pady=(1, 2))

        card = tk.Frame(
            container,
            bg=VINTAGE_CARD_BG,
            highlightbackground=VINTAGE_CARD_BORDER,
            highlightthickness=2,
            padx=12,
            pady=8,
        )
        card.pack(fill=tk.BOTH, expand=True)
        return card

    def _build_ui(self):
        # 0. MAIN HEADER
        top_bar = tk.Frame(self.root, bg=VINTAGE_BG)
        top_bar.pack(fill=tk.X, padx=20, pady=(8, 2))

        tk.Label(
            top_bar,
            text="SMART OPERATION",
            font=("Trebuchet MS", 14, "bold"),
            bg=VINTAGE_BG,
            fg=VINTAGE_TEXT_HEAD,
        ).pack(side=tk.LEFT)

        tk.Label(
            top_bar,
            text="HIS AUTOMATION CONSOLE // v0.4.1",
            font=("Segoe UI", 9, "bold"),
            bg=VINTAGE_BG,
            fg=VINTAGE_TEXT_MUTED,
        ).pack(side=tk.LEFT, padx=(10, 0))

        # Nút cài đặt & thu nhỏ khay ở góc trên bên phải
        Retro3DButton(
            top_bar,
            text="⚙️ CÀI ĐẶT PHÍM TẮT",
            width=140,
            height=30,
            top_color=BTN_BEIGE_TOP,
            bot_color=BTN_BEIGE_BOT,
            text_color=BTN_BEIGE_TXT,
            command=self._cmd_open_settings,
        ).pack(side=tk.RIGHT, padx=(4, 0))

        Retro3DButton(
            top_bar,
            text="🔻 THU VÀO KHAY",
            width=120,
            height=30,
            top_color=BTN_BLUE_TOP,
            bot_color=BTN_BLUE_BOT,
            text_color=BTN_BLUE_TXT,
            command=self._hide_to_tray,
        ).pack(side=tk.RIGHT, padx=(4, 0))

        # ==========================================
        # 1. KHỐI "SLIDE" (ĐIỀU KHIỂN & ĐA KỊCH BẢN)
        # ==========================================
        slide_card = self._create_section_card(self.root, "SLIDE")

        # Rãnh HUD trạng thái
        self.hud_track = tk.Frame(
            slide_card,
            bg=VINTAGE_INNER_GROOVE,
            highlightbackground=VINTAGE_CARD_BORDER,
            highlightthickness=1,
            padx=10,
            pady=5,
        )
        self.hud_track.pack(fill=tk.X, pady=(0, 6))

        self.hud_status_lbl = tk.Label(
            self.hud_track,
            text="● STATUS: SẴN SÀNG (READY)   │   HỌC: [F8]   │   DỪNG KHẨN CẤP: [ESC]",
            font=("Trebuchet MS", 9, "bold"),
            bg=VINTAGE_INNER_GROOVE,
            fg=BTN_GREEN_TXT,
        )
        self.hud_status_lbl.pack(anchor="center")

        # Hàng chọn Kịch bản (Script Profile Selector)
        profile_row = tk.Frame(slide_card, bg=VINTAGE_CARD_BG)
        profile_row.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            profile_row,
            text="📋 KỊCH BẢN HIỆN TẠI:",
            font=FONT_TITLE,
            bg=VINTAGE_CARD_BG,
            fg=VINTAGE_TEXT_HEAD,
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.profile_combo_var = tk.StringVar()
        self.profile_combo = ttk.Combobox(
            profile_row,
            textvariable=self.profile_combo_var,
            width=36,
            state="readonly",
            font=("Segoe UI", 9, "bold"),
        )
        self.profile_combo.pack(side=tk.LEFT, padx=(0, 8))
        self.profile_combo.bind("<<ComboboxSelected>>", self._on_profile_selected)

        # Các nút quản lý kịch bản nhanh
        Retro3DButton(profile_row, text="+ THÊM KỊCH BẢN", width=120, height=30, top_color=BTN_GREEN_TOP, bot_color=BTN_GREEN_BOT, text_color=BTN_GREEN_TXT, command=self._cmd_add_profile).pack(side=tk.LEFT, padx=3)
        Retro3DButton(profile_row, text="✏️ ĐỔI PHÍM TẮT", width=110, height=30, top_color=BTN_YELLOW_TOP, bot_color=BTN_YELLOW_BOT, text_color=BTN_YELLOW_TXT, command=self._cmd_edit_profile_hotkey).pack(side=tk.LEFT, padx=3)
        Retro3DButton(profile_row, text="🗑️ XÓA KỊCH BẢN", width=110, height=30, top_color=BTN_RED_TOP, bot_color=BTN_RED_BOT, text_color=BTN_RED_TXT, command=self._cmd_delete_profile).pack(side=tk.LEFT, padx=3)

        # Hàng cấu hình Tốc độ & Lặp
        ctrl_row = tk.Frame(slide_card, bg=VINTAGE_CARD_BG)
        ctrl_row.pack(fill=tk.X)

        tk.Label(ctrl_row, text="TỐC ĐỘ PHÁT:", font=FONT_TITLE, bg=VINTAGE_CARD_BG, fg=VINTAGE_TEXT_HEAD).pack(side=tk.LEFT, padx=(0, 6))

        self.speed_buttons = {}
        for spd_label in ["0.5x", "0.8x", "1.0x", "1.25x", "1.5x", "2.0x"]:
            is_default = (spd_label == "1.0x")
            btn = Retro3DButton(
                ctrl_row,
                text=spd_label,
                width=48,
                height=26,
                top_color=BTN_RED_TOP if is_default else BTN_BEIGE_TOP,
                bot_color=BTN_RED_BOT if is_default else BTN_BEIGE_BOT,
                text_color=BTN_RED_TXT if is_default else BTN_BEIGE_TXT,
                command=lambda s=spd_label: self._set_speed(s),
                radius=6,
            )
            btn.pack(side=tk.LEFT, padx=2)
            self.speed_buttons[spd_label] = btn

        tk.Label(ctrl_row, text="   LẶP:", font=FONT_TITLE, bg=VINTAGE_CARD_BG, fg=VINTAGE_TEXT_HEAD).pack(side=tk.LEFT, padx=(10, 4))
        self.entry_loop = tk.Entry(ctrl_row, textvariable=self.loop_count_var, width=4, bg=VINTAGE_INNER_GROOVE, fg=VINTAGE_TEXT_HEAD, font=("Segoe UI", 9, "bold"), relief=tk.FLAT)
        self.entry_loop.pack(side=tk.LEFT)

        tk.Label(ctrl_row, text="   NGHỈ (s):", font=FONT_TITLE, bg=VINTAGE_CARD_BG, fg=VINTAGE_TEXT_HEAD).pack(side=tk.LEFT, padx=(6, 4))
        self.entry_delay = tk.Entry(ctrl_row, textvariable=self.loop_delay_var, width=4, bg=VINTAGE_INNER_GROOVE, fg=VINTAGE_TEXT_HEAD, font=("Segoe UI", 9, "bold"), relief=tk.FLAT)
        self.entry_delay.pack(side=tk.LEFT)

        tk.Checkbutton(ctrl_row, text="Bỏ qua di chuột thừa", variable=self.ignore_movement_var, font=FONT_BODY, bg=VINTAGE_CARD_BG, fg=VINTAGE_TEXT_BODY, selectcolor=VINTAGE_INNER_GROOVE).pack(side=tk.LEFT, padx=(12, 0))
        tk.Checkbutton(ctrl_row, text="Đếm ngược 3s", variable=self.countdown_var, font=FONT_BODY, bg=VINTAGE_CARD_BG, fg=VINTAGE_TEXT_BODY, selectcolor=VINTAGE_INNER_GROOVE).pack(side=tk.LEFT, padx=(6, 0))

        # ==========================================
        # 2. KHỐI "PRESS" (NÚT BẤM 3D MATTE THEO ẢNH)
        # ==========================================
        press_card = self._create_section_card(self.root, "PRESS")

        row1 = tk.Frame(press_card, bg=VINTAGE_CARD_BG)
        row1.pack(fill=tk.X, pady=(2, 5))

        self.btn_rec = Retro3DButton(
            row1,
            text=f"HỌC THAO TÁC ({self.manager.hotkey_record_str})",
            width=165,
            height=42,
            top_color=BTN_YELLOW_TOP,
            bot_color=BTN_YELLOW_BOT,
            text_color=BTN_YELLOW_TXT,
            command=self._cmd_start_recording,
        )
        self.btn_rec.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_play = Retro3DButton(
            row1,
            text="CHẠY KỊCH BẢN (F9)",
            width=175,
            height=42,
            top_color=BTN_GREEN_TOP,
            bot_color=BTN_GREEN_BOT,
            text_color=BTN_GREEN_TXT,
            command=self._cmd_start_playing,
        )
        self.btn_play.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_stop = Retro3DButton(
            row1,
            text="DỪNG HỌC",
            width=120,
            height=42,
            top_color=BTN_BLUE_TOP,
            bot_color=BTN_BLUE_BOT,
            text_color=BTN_BLUE_TXT,
            command=self._cmd_stop_recording,
        )
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 8))
        self.btn_stop.configure_state("disabled")

        self.btn_panic = Retro3DButton(
            row1,
            text=f"DỪNG KHẨN CẤP ({self.manager.hotkey_panic_str})",
            width=180,
            height=42,
            top_color=BTN_RED_TOP,
            bot_color=BTN_RED_BOT,
            text_color=BTN_RED_TXT,
            command=self._cmd_emergency_stop,
        )
        self.btn_panic.pack(side=tk.RIGHT)

        row2 = tk.Frame(press_card, bg=VINTAGE_CARD_BG)
        row2.pack(fill=tk.X, pady=(3, 2))

        Retro3DButton(row2, text="MỞ .JSON", width=95, height=32, top_color=BTN_BLUE_TOP, bot_color=BTN_BLUE_BOT, text_color=BTN_BLUE_TXT, command=self._cmd_load_file).pack(side=tk.LEFT, padx=(0, 6))
        Retro3DButton(row2, text="LƯU .JSON", width=95, height=32, top_color=BTN_YELLOW_TOP, bot_color=BTN_YELLOW_BOT, text_color=BTN_YELLOW_TXT, command=self._cmd_save_file).pack(side=tk.LEFT, padx=(0, 6))
        Retro3DButton(row2, text="SỬA ĐỘ TRỄ", width=105, height=32, top_color=BTN_GREEN_TOP, bot_color=BTN_GREEN_BOT, text_color=BTN_GREEN_TXT, command=self._cmd_edit_delay).pack(side=tk.LEFT, padx=(0, 6))
        Retro3DButton(row2, text="XÓA BƯỚC", width=95, height=32, top_color=BTN_BEIGE_TOP, bot_color=BTN_BEIGE_BOT, text_color=BTN_BEIGE_TXT, command=self._cmd_delete_selected_action).pack(side=tk.LEFT, padx=(0, 6))
        Retro3DButton(row2, text="XÓA HẾT BƯỚC", width=110, height=32, top_color=BTN_RED_TOP, bot_color=BTN_RED_BOT, text_color=BTN_RED_TXT, command=self._cmd_clear_actions).pack(side=tk.RIGHT)

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
        self.tree.column("detail", width=500, anchor="w")

        scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview, style="RetroHardware.Vertical.TScrollbar")
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        stats_bar = tk.Frame(scroll_card, bg=VINTAGE_CARD_BG)
        stats_bar.pack(fill=tk.X, pady=(5, 0))

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
            text="💡 Gợi ý: Thu nhỏ ứng dụng vào khay hệ thống, chuyển sang phần mềm HIS và nhấn tổ hợp phím đã gán để chạy!",
            font=("Segoe UI", 8, "italic"),
            bg=VINTAGE_CARD_BG,
            fg=VINTAGE_TEXT_MUTED,
        ).pack(side=tk.RIGHT)

        # Đồng bộ danh sách kịch bản ban đầu
        self._refresh_profile_list()

    # ==========================================
    # QUẢN LÝ KHAY HỆ THỐNG (SYSTEM TRAY)
    # ==========================================
    def _setup_system_tray(self):
        """Khởi tạo icon khay hệ thống Windows (chạy ngầm)."""
        icon_img = create_tray_icon_image()

        def _action_open(icon, item):
            self.root.after(0, self._show_from_tray)

        def _action_panic(icon, item):
            self.manager.stop_playing()

        def _action_exit(icon, item):
            self._exit_app()

        tray_menu = pystray.Menu(
            pystray.MenuItem("📌 Mở giao diện chính", _action_open, default=True),
            pystray.MenuItem("🛑 Dừng khẩn cấp (ESC)", _action_panic),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Thoát ứng dụng", _action_exit),
        )

        self.tray_icon = pystray.Icon(
            "SmartOperation",
            icon_img,
            "Smart Operation - HIS Bot v0.4.1 (Đang chạy ngầm)",
            tray_menu,
        )

        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _hide_to_tray(self):
        """Ẩn cửa sổ xuống khay hệ thống."""
        self.root.withdraw()

    def _show_from_tray(self):
        """Khôi phục cửa sổ từ khay hệ thống."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _on_window_close(self):
        """Khi người dùng bấm nút [X] ở góc cửa sổ."""
        if self.manager.minimize_to_tray_on_close:
            self._hide_to_tray()
        else:
            self._exit_app()

    def _exit_app(self):
        """Thoát hoàn toàn ứng dụng."""
        self.manager.stop_global_hotkeys()
        self.manager.stop_playing()
        if self.countdown_timer:
            self.root.after_cancel(self.countdown_timer)
        if self.tray_icon:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
        self.root.after(0, self.root.destroy)

    # ==========================================
    # CÀI ĐẶT TỔ HỢP PHÍM (HOTKEY SETTINGS)
    # ==========================================
    def _cmd_open_settings(self):
        """Mở cửa sổ cài đặt tổ hợp phím hệ thống."""
        win = tk.Toplevel(self.root)
        win.title("CÀI ĐẶT TỔ HỢP PHÍM & HỆ THỐNG")
        win.geometry("450x330")
        win.minsize(420, 300)
        win.configure(bg=VINTAGE_BG)
        win.transient(self.root)
        win.grab_set()

        card = tk.Frame(win, bg=VINTAGE_CARD_BG, highlightbackground=VINTAGE_CARD_BORDER, highlightthickness=2, padx=16, pady=14)
        card.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        tk.Label(card, text="⚙️ CÀI ĐẶT HỆ THỐNG", font=FONT_HEADER, bg=VINTAGE_CARD_BG, fg=VINTAGE_TEXT_HEAD).pack(anchor="w", pady=(0, 10))

        # Phím bắt đầu học
        f1 = tk.Frame(card, bg=VINTAGE_CARD_BG)
        f1.pack(fill=tk.X, pady=4)
        tk.Label(f1, text="Phím Bắt đầu / Dừng học thao tác:", font=FONT_BODY, bg=VINTAGE_CARD_BG, fg=VINTAGE_TEXT_HEAD).pack(side=tk.LEFT)
        entry_rec = tk.Entry(f1, font=("Segoe UI", 9, "bold"), width=12, justify="center")
        entry_rec.insert(0, self.manager.hotkey_record_str)
        entry_rec.pack(side=tk.RIGHT)

        # Phím dừng khẩn cấp
        f2 = tk.Frame(card, bg=VINTAGE_CARD_BG)
        f2.pack(fill=tk.X, pady=4)
        tk.Label(f2, text="Phím Dừng khẩn cấp (Panic Stop):", font=FONT_BODY, bg=VINTAGE_CARD_BG, fg=VINTAGE_TEXT_HEAD).pack(side=tk.LEFT)
        entry_panic = tk.Entry(f2, font=("Segoe UI", 9, "bold"), width=12, justify="center")
        entry_panic.insert(0, self.manager.hotkey_panic_str)
        entry_panic.pack(side=tk.RIGHT)

        # Checkbox thu nhỏ khay
        tray_var = tk.BooleanVar(value=self.manager.minimize_to_tray_on_close)
        chk_tray = tk.Checkbutton(
            card,
            text="Thu nhỏ xuống Khay hệ thống khi bấm nút đóng [X]",
            variable=tray_var,
            font=FONT_BODY,
            bg=VINTAGE_CARD_BG,
            fg=VINTAGE_TEXT_HEAD,
            selectcolor=VINTAGE_INNER_GROOVE,
        )
        chk_tray.pack(anchor="w", pady=(10, 10))

        tk.Label(
            card,
            text="Gợi ý: Có thể dùng phím đơn (F8, F9, ESC,...) hoặc tổ hợp (Ctrl+F1, Alt+1, Ctrl+Shift+K).",
            font=("Segoe UI", 8, "italic"),
            bg=VINTAGE_CARD_BG,
            fg=VINTAGE_TEXT_MUTED,
            wraplength=380,
            justify="left",
        ).pack(anchor="w", pady=(0, 10))

        def _save():
            new_rec = entry_rec.get().strip().upper()
            new_panic = entry_panic.get().strip().upper()
            if not new_rec or not new_panic:
                messagebox.showwarning("Lỗi", "Vui lòng không để trống phím tắt!", parent=win)
                return
            self.manager.hotkey_record_str = new_rec
            self.manager.hotkey_panic_str = new_panic
            self.manager.minimize_to_tray_on_close = tray_var.get()
            self.manager.save_library()
            self.manager.reload_global_hotkeys()

            self.btn_rec.set_text(f"HỌC THAO TÁC ({new_rec})")
            self.btn_panic.set_text(f"DỪNG KHẨN CẤP ({new_panic})")
            win.destroy()
            messagebox.showinfo("Thành công", "Đã cập nhật cài đặt phím tắt hệ thống!")

        btn_row = tk.Frame(card, bg=VINTAGE_CARD_BG)
        btn_row.pack(fill=tk.X, pady=(6, 0))
        Retro3DButton(btn_row, text="💾 LƯU CÀI ĐẶT", width=120, height=34, top_color=BTN_GREEN_TOP, bot_color=BTN_GREEN_BOT, text_color=BTN_GREEN_TXT, command=_save).pack(side=tk.RIGHT, padx=4)
        Retro3DButton(btn_row, text="HỦY", width=80, height=34, top_color=BTN_BEIGE_TOP, bot_color=BTN_BEIGE_BOT, text_color=BTN_BEIGE_TXT, command=win.destroy).pack(side=tk.RIGHT)

    # ==========================================
    # QUẢN LÝ ĐA KỊCH BẢN (MULTI-SCRIPT PROFILES)
    # ==========================================
    def _refresh_profile_list(self):
        """Cập nhật dropdown chọn kịch bản."""
        display_values = []
        cur_idx = 0
        active = self.manager.get_active_profile()

        for idx, p in enumerate(self.manager.profiles):
            hk_text = f"[{p.hotkey}]" if p.hotkey else "[Chưa gán]"
            total = len(p.actions)
            display_values.append(f"{p.name} - Phím: {hk_text} ({total} bước)")
            if active and p.id == active.id:
                cur_idx = idx

        self.profile_combo["values"] = display_values
        if display_values:
            self.profile_combo.current(cur_idx)
            self._load_active_profile_ui()

    def _on_profile_selected(self, event):
        idx = self.profile_combo.current()
        if 0 <= idx < len(self.manager.profiles):
            sel_profile = self.manager.profiles[idx]
            self.manager.set_active_profile(sel_profile.id)
            self._load_active_profile_ui()

    def _load_active_profile_ui(self):
        """Nạp dữ liệu của profile đang chọn lên bảng."""
        active = self.manager.get_active_profile()
        if not active:
            return
        # Cập nhật nút Play với phím tắt tương ứng
        self.btn_play.set_text(f"CHẠY ({active.hotkey})")
        self.speed_var.set(f"{active.speed:.1f}x")
        self.loop_count_var.set(str(active.loop_count))
        self.loop_delay_var.set(str(active.loop_delay))
        self._refresh_action_tree()

    def _cmd_add_profile(self):
        """Thêm kịch bản mới."""
        name = simpledialog.askstring("THÊM KỊCH BẢN MỚI", "Nhập tên cho kịch bản mới:", parent=self.root)
        if not name or not name.strip():
            return
        hotkey = simpledialog.askstring("GÁN PHÍM TẮT", f"Nhập tổ hợp phím kích hoạt cho '{name}' (VD: F9, F10, Ctrl+F1):", initialvalue="F10", parent=self.root)
        if not hotkey:
            hotkey = "F10"

        new_profile = ScriptProfile(
            name=name.strip(),
            hotkey=hotkey.strip().upper(),
            actions=[],
            speed=1.0,
            loop_count=1,
            loop_delay=1.0,
        )
        self.manager.profiles.append(new_profile)
        self.manager.set_active_profile(new_profile.id)
        self.manager.save_library()
        self.manager.reload_global_hotkeys()
        self._refresh_profile_list()
        messagebox.showinfo("Thành công", f"Đã thêm kịch bản '{name}' với phím tắt [{hotkey.strip().upper()}]!")

    def _cmd_edit_profile_hotkey(self):
        """Đổi tên hoặc phím tắt của kịch bản hiện tại."""
        active = self.manager.get_active_profile()
        if not active:
            return
        new_name = simpledialog.askstring("ĐỔI TÊN KỊCH BẢN", "Tên kịch bản:", initialvalue=active.name, parent=self.root)
        if new_name and new_name.strip():
            active.name = new_name.strip()

        new_hk = simpledialog.askstring("ĐỔI PHÍM TẮT KÍCH HOẠT", f"Tổ hợp phím cho '{active.name}' (VD: F9, F10, Ctrl+F1):", initialvalue=active.hotkey, parent=self.root)
        if new_hk and new_hk.strip():
            active.hotkey = new_hk.strip().upper()

        self.manager.save_library()
        self.manager.reload_global_hotkeys()
        self._refresh_profile_list()

    def _cmd_delete_profile(self):
        """Xóa kịch bản đang chọn."""
        if len(self.manager.profiles) <= 1:
            messagebox.showwarning("Cảnh báo", "Bạn phải giữ lại ít nhất 1 kịch bản!")
            return
        active = self.manager.get_active_profile()
        if not active:
            return
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa kịch bản '{active.name}'?"):
            self.manager.profiles = [p for p in self.manager.profiles if p.id != active.id]
            self.manager.active_profile_id = self.manager.profiles[0].id
            self.manager.save_library()
            self.manager.reload_global_hotkeys()
            self._refresh_profile_list()

    # ==========================================
    # LOGIC ĐIỀU KHIỂN & CẬP NHẬT TRẠNG THÁI
    # ==========================================
    def _set_speed(self, spd_text: str):
        self.speed_var.set(spd_text)
        active = self.manager.get_active_profile()
        if active:
            active.speed = self._parse_speed()
            self.manager.save_library()

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
        self._refresh_profile_list()

    def _cmd_start_playing(self):
        active = self.manager.get_active_profile()
        if not active or not active.actions:
            messagebox.showwarning("THÔNG BÁO", "Kịch bản hiện tại chưa có thao tác nào!\nNhấn F8 để học hoặc mở file kịch bản.")
            return
        active.speed = self._parse_speed()
        active.loop_count = self._parse_loop_count()
        active.loop_delay = self._parse_loop_delay()
        self.manager.start_playing_profile(active)

    def _cmd_emergency_stop(self):
        if self.countdown_timer:
            self.root.after_cancel(self.countdown_timer)
            self.countdown_timer = None
        self.manager.stop_playing()

    def _set_hud(self, text: str, fg: str):
        self.hud_status_lbl.configure(text=text, fg=fg)

    def _on_manager_state_changed(self, new_state: str):
        self.root.after(0, lambda: self._handle_state_ui(new_state))

    def _on_profile_triggered(self, profile: ScriptProfile):
        """Được gọi khi người dùng bấm phím tắt của một kịch bản từ bất kỳ đâu."""
        self.root.after(0, lambda: self._refresh_profile_list())

    def _handle_state_ui(self, state: str):
        active = self.manager.get_active_profile()
        p_name = active.name if active else "Mặc định"
        p_hk = active.hotkey if active else "F9"

        if state == MacroManager.STATE_IDLE:
            self._set_hud(
                f"● SẴN SÀNG │ KỊCH BẢN: '{p_name}' [{p_hk}] │ HỌC: [{self.manager.hotkey_record_str}] │ DỪNG: [{self.manager.hotkey_panic_str}]",
                fg=BTN_GREEN_TXT,
            )
            self.btn_rec.configure_state("normal")
            self.btn_stop.configure_state("disabled")
            self.btn_play.configure_state("normal")
            self._refresh_action_tree()

        elif state == MacroManager.STATE_RECORDING:
            self._set_hud(
                f"🔴 [REC] ĐANG GHI THAO TÁC CHO '{p_name}'... LÀM TRÊN HIS XONG NHẤN [{self.manager.hotkey_record_str}] HOẶC [{self.manager.hotkey_panic_str}]",
                fg=BTN_RED_BOT,
            )
            self.btn_rec.configure_state("disabled")
            self.btn_stop.configure_state("normal")
            self.btn_play.configure_state("disabled")

        elif state == MacroManager.STATE_PLAYING:
            self._set_hud(
                f"🔵 [RUN] ĐANG THỰC HIỆN KỊCH BẢN '{p_name}'... NHẤN [{self.manager.hotkey_panic_str}] ĐỂ DỪNG NGAY!",
                fg=BTN_BLUE_TXT,
            )
            self.btn_rec.configure_state("disabled")
            self.btn_stop.configure_state("disabled")
            self.btn_play.configure_state("disabled")

    def _on_action_recorded(self, action: MacroAction, count: int):
        self.root.after(0, lambda: self._add_action_to_tree(action, count))

    def _on_player_step(self, step: int, total: int, cur_loop: int, total_loops: int):
        active = self.manager.get_active_profile()
        p_name = active.name if active else ""
        loop_str = f"VÒNG {cur_loop}/{total_loops}" if total_loops > 0 else f"VÒNG {cur_loop} (VÔ HẠN)"
        txt = f"🔵 [RUN '{p_name}'] {loop_str} ── BƯỚC {step:02d}/{total:02d} │ NHẤN [{self.manager.hotkey_panic_str}] ĐỂ DỪNG"
        self.root.after(0, lambda: self._set_hud(txt, fg=BTN_BLUE_TXT))

    def _on_player_finished(self, success: bool, aborted: bool):
        active = self.manager.get_active_profile()
        p_name = active.name if active else ""
        if aborted:
            msg = f"ĐÃ DỪNG KHẨN CẤP '{p_name}' THEO LỆNH ({self.manager.hotkey_panic_str})"
            self.root.after(0, lambda: self._set_hud(f"⚠️ {msg}", fg=BTN_YELLOW_TXT))
        else:
            msg = f"HOÀN TẤT KỊCH BẢN '{p_name}' THÀNH CÔNG!"
            self.root.after(0, lambda: self._set_hud(f"⭐ {msg}", fg=BTN_GREEN_TXT))

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
        active = self.manager.get_active_profile()
        if not active:
            return
        for idx, act in enumerate(active.actions, start=1):
            t_name, detail, delay_str = self._format_action_display(act)
            self.tree.insert("", tk.END, values=(f"{idx:02d}", delay_str, t_name, detail))
        self._update_stats()

    def _update_stats(self):
        active = self.manager.get_active_profile()
        actions = active.actions if active else []
        total = len(actions)
        total_time = sum(act.delay for act in actions)
        self.lbl_stats.configure(text=f"[ THAO TÁC: {total:03d} ]   [ TỔNG THỜI GIAN: {total_time:.2f}s ]")

    def _cmd_delete_selected_action(self):
        active = self.manager.get_active_profile()
        if not active:
            return
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("THÔNG BÁO", "Hãy chọn một dòng trong bảng để xóa!")
            return
        idx = self.tree.index(selected[0])
        if 0 <= idx < len(active.actions):
            del active.actions[idx]
            self.manager.save_library()
            self._refresh_action_tree()

    def _cmd_edit_delay(self):
        active = self.manager.get_active_profile()
        if not active:
            return
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("THÔNG BÁO", "Hãy chọn một dòng trong bảng để sửa thời gian chờ!")
            return
        idx = self.tree.index(selected[0])
        action = active.actions[idx]

        new_val = simpledialog.askfloat(
            "SỬA ĐỘ TRỄ",
            f"Nhập thời gian chờ trước bước #{idx + 1} (giây):",
            initialvalue=action.delay,
            minvalue=0.0,
            maxvalue=300.0,
        )
        if new_val is not None:
            action.delay = round(new_val, 4)
            self.manager.save_library()
            self._refresh_action_tree()

    def _cmd_clear_actions(self):
        active = self.manager.get_active_profile()
        if not active or not active.actions:
            return
        if messagebox.askyesno("XÁC NHẬN", f"Bạn có chắc muốn xóa tất cả thao tác của '{active.name}'?"):
            active.actions = []
            self.manager.save_library()
            self._refresh_action_tree()

    def _cmd_save_file(self):
        active = self.manager.get_active_profile()
        if not active or not active.actions:
            messagebox.showwarning("CẢNH BÁO", "Kịch bản hiện tại chưa có thao tác nào để lưu!")
            return

        file_path = filedialog.asksaveasfilename(
            title="LƯU KỊCH BẢN THAO TÁC",
            defaultextension=".json",
            filetypes=[("JSON Macro Script", "*.json"), ("All Files", "*.*")],
            initialfile=f"{active.name.lower().replace(' ', '_')}.json",
        )
        if not file_path:
            return

        try:
            MacroStorage.save_to_file(
                active.actions,
                file_path,
                metadata={"name": active.name, "hotkey": active.hotkey, "speed": active.speed},
            )
            messagebox.showinfo("THÀNH CÔNG", f"Đã xuất kịch bản ra file:\n{os.path.basename(file_path)}")
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
            active = self.manager.get_active_profile()
            if active:
                active.actions = actions
                self.manager.save_library()
                self._refresh_action_tree()
                messagebox.showinfo("THÀNH CÔNG", f"Đã nạp {len(actions)} thao tác từ:\n{os.path.basename(file_path)}")
        except Exception as ex:
            messagebox.showerror("LỖI KHI MỞ", str(ex))


def run_app():
    root = tk.Tk()
    app = SmartOperationApp(root)
    root.mainloop()


if __name__ == "__main__":
    run_app()
