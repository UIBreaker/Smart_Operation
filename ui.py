"""
Smart Operation - Pixel Art / Retro Gaming Edition
Giao diện phong cách Pixel Art / 8-bit Cyberpunk cổ điển cực đẹp và sắc nét.
Tối ưu cho màn hình độ phân giải cao và các thao tác lặp đi lặp lại trên phần mềm HIS.
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
# PIXEL RETRO COLOR PALETTE
# ==========================================
PIXEL_BG = "#0d0f18"           # Nền đen vũ trụ arcade
PIXEL_PANEL = "#161828"        # Nền hộp bảng điều khiển
PIXEL_PANEL_ALT = "#1d2035"    # Nền phụ
PIXEL_BORDER = "#2b2e4c"       # Viền pixel tối
PIXEL_CYAN = "#00f0ff"         # Xanh neon cyber
PIXEL_GREEN = "#00ff88"        # Xanh lá 8-bit (Player 1 / Ready)
PIXEL_RED = "#ff2a5f"          # Đỏ pixel (Laser / Record)
PIXEL_YELLOW = "#ffd600"       # Vàng coin arcade
PIXEL_PURPLE = "#b55fe6"       # Tím neon synthwave
PIXEL_WHITE = "#f8f9fa"        # Trắng sáng
PIXEL_MUTED = "#868fa6"        # Xám bạc
PIXEL_FONT = "Consolas"        # Phông chữ bitmap monospace sắc nét chuẩn pixel


class PixelButton(tk.Button):
    """Nút bấm phong cách pixel retro với viền khối 3D arcade nổi bật."""
    def __init__(self, master=None, bg_color="#2b2e4c", fg_color="#ffffff", active_bg="#3d4168", **kwargs):
        super().__init__(
            master,
            font=(PIXEL_FONT, 10, "bold"),
            bg=bg_color,
            fg=fg_color,
            activebackground=active_bg,
            activeforeground=fg_color,
            relief=tk.RAISED,
            bd=3,
            cursor="hand2",
            **kwargs,
        )


class SmartOperationApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("👾 SMART OPERATION // v0.2.0 [PIXEL EDITION]")
        self.root.geometry("860x720")
        self.root.minsize(800, 650)
        self.root.configure(bg=PIXEL_BG)

        # Khởi tạo MacroManager
        self.manager = MacroManager()

        # Biến cấu hình
        self.speed_var = tk.StringVar(value="1.0x (CHUẨN)")
        self.loop_count_var = tk.StringVar(value="1")
        self.loop_delay_var = tk.StringVar(value="1.0")
        self.ignore_movement_var = tk.BooleanVar(value=True)  # Mặc định lọc bỏ chuột thừa
        self.countdown_var = tk.BooleanVar(value=True)

        self.countdown_timer = None
        self.current_file_path = None

        # Kết nối Callbacks từ Core Manager
        self.manager.on_state_changed = self._on_manager_state_changed
        self.manager.on_action_recorded = self._on_action_recorded
        self.manager.on_step = self._on_player_step
        self.manager.on_play_finished = self._on_player_finished

        # Kích hoạt DPI Awareness
        enable_dpi_awareness()

        # Cài đặt Theme & Giao diện
        self._setup_retro_styles()
        self._build_pixel_ui()

        # Lắng nghe phím tắt toàn hệ thống
        self.manager.start_global_hotkeys()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _setup_retro_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Cấu hình Treeview phong cách Retro Terminal
        style.configure(
            "Retro.Treeview",
            background=PIXEL_PANEL,
            foreground=PIXEL_CYAN,
            fieldbackground=PIXEL_PANEL,
            font=(PIXEL_FONT, 9),
            rowheight=26,
            borderwidth=0,
        )
        style.configure(
            "Retro.Treeview.Heading",
            background="#21243a",
            foreground=PIXEL_YELLOW,
            font=(PIXEL_FONT, 9, "bold"),
            relief=tk.FLAT,
        )
        style.map(
            "Retro.Treeview",
            background=[("selected", PIXEL_RED)],
            foreground=[("selected", PIXEL_WHITE)],
        )

        # Scrollbar tối
        style.configure(
            "Retro.Vertical.TScrollbar",
            background=PIXEL_PANEL_ALT,
            troughcolor=PIXEL_BG,
            arrowcolor=PIXEL_CYAN,
            borderwidth=0,
        )

    def _build_pixel_ui(self):
        # 1. RETRO ARCADE HEADER
        header_card = tk.Frame(
            self.root,
            bg=PIXEL_PANEL,
            highlightbackground=PIXEL_CYAN,
            highlightthickness=2,
            padx=14,
            pady=10,
        )
        header_card.pack(fill=tk.X, padx=14, pady=(12, 6))

        top_row = tk.Frame(header_card, bg=PIXEL_PANEL)
        top_row.pack(fill=tk.X)

        title_lbl = tk.Label(
            top_row,
            text="👾 SMART OPERATION // RETRO HIS AUTOMATION",
            font=(PIXEL_FONT, 14, "bold"),
            bg=PIXEL_PANEL,
            fg=PIXEL_CYAN,
        )
        title_lbl.pack(side=tk.LEFT)

        tag_lbl = tk.Label(
            top_row,
            text="[ 8-BIT BOT // v0.2.0 ]",
            font=(PIXEL_FONT, 10, "bold"),
            bg=PIXEL_PANEL,
            fg=PIXEL_YELLOW,
        )
        tag_lbl.pack(side=tk.RIGHT)

        sub_lbl = tk.Label(
            header_card,
            text=">> HỆ THỐNG GHI NHỚ & TỰ ĐỘNG HÓA THAO TÁC: ĐIỀN MẪU • KÝ SỐ • HOÀN THÀNH KHÁM <<",
            font=(PIXEL_FONT, 8, "bold"),
            bg=PIXEL_PANEL,
            fg=PIXEL_MUTED,
        )
        sub_lbl.pack(anchor="w", pady=(4, 0))

        # 2. ARCADE HUD STATUS CARD
        self.hud_frame = tk.Frame(
            self.root,
            bg="#11291f",
            highlightbackground=PIXEL_GREEN,
            highlightthickness=2,
            padx=12,
            pady=8,
        )
        self.hud_frame.pack(fill=tk.X, padx=14, pady=4)

        self.hud_status_lbl = tk.Label(
            self.hud_frame,
            text="● STATUS: SẴN SÀNG (READY)   │   [F8] HỌC THAO TÁC   │   [F9] CHẠY BOT   │   [ESC] DỪNG KHẨN CẤP",
            font=(PIXEL_FONT, 10, "bold"),
            bg="#11291f",
            fg=PIXEL_GREEN,
        )
        self.hud_status_lbl.pack(anchor="center")

        # 3. CONTROL BUTTONS (RETRO ARCADE PUSH BUTTONS)
        btn_bar = tk.Frame(self.root, bg=PIXEL_BG)
        btn_bar.pack(fill=tk.X, padx=14, pady=6)

        self.btn_rec = PixelButton(
            btn_bar,
            text="🔴 [F8] HỌC THAO TÁC",
            bg_color=PIXEL_RED,
            active_bg="#c9184a",
            command=self._cmd_start_recording,
            padx=12,
            pady=6,
        )
        self.btn_rec.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_stop = PixelButton(
            btn_bar,
            text="⏹ DỪNG GHI (F8)",
            bg_color="#363952",
            fg_color=PIXEL_MUTED,
            active_bg="#25283b",
            state=tk.DISABLED,
            command=self._cmd_stop_recording,
            padx=10,
            pady=6,
        )
        self.btn_stop.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_play = PixelButton(
            btn_bar,
            text="▶ [F9] CHẠY THAO TÁC",
            bg_color="#0096c7",
            active_bg="#0077b6",
            command=self._cmd_start_playing,
            padx=12,
            pady=6,
        )
        self.btn_play.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_panic = PixelButton(
            btn_bar,
            text="🛑 [ESC] DỪNG KHẨN CẤP",
            bg_color="#b7094c",
            active_bg="#890620",
            command=self._cmd_emergency_stop,
            padx=14,
            pady=6,
        )
        self.btn_panic.pack(side=tk.RIGHT)

        # 4. CONFIG SETTINGS PANEL
        cfg_frame = tk.Frame(
            self.root,
            bg=PIXEL_PANEL,
            highlightbackground=PIXEL_BORDER,
            highlightthickness=2,
            padx=12,
            pady=10,
        )
        cfg_frame.pack(fill=tk.X, padx=14, pady=4)

        # Row 1 Settings
        r1 = tk.Frame(cfg_frame, bg=PIXEL_PANEL)
        r1.pack(fill=tk.X)

        tk.Label(r1, text="⚡ TỐC ĐỘ:", font=(PIXEL_FONT, 9, "bold"), bg=PIXEL_PANEL, fg=PIXEL_YELLOW).pack(side=tk.LEFT, padx=(0, 4))
        self.combo_speed = ttk.Combobox(
            r1,
            textvariable=self.speed_var,
            values=["0.5x (Chậm)", "0.8x (An toàn)", "1.0x (CHUẨN)", "1.25x (Nhanh)", "1.5x (Rất nhanh)", "2.0x"],
            width=15,
            state="readonly",
            font=(PIXEL_FONT, 9),
        )
        self.combo_speed.pack(side=tk.LEFT, padx=(0, 16))

        tk.Label(r1, text="🔁 SỐ LẦN LẶP:", font=(PIXEL_FONT, 9, "bold"), bg=PIXEL_PANEL, fg=PIXEL_YELLOW).pack(side=tk.LEFT, padx=(0, 4))
        self.entry_loop = tk.Entry(
            r1,
            textvariable=self.loop_count_var,
            width=5,
            bg="#21243a",
            fg=PIXEL_WHITE,
            insertbackground=PIXEL_CYAN,
            font=(PIXEL_FONT, 9, "bold"),
            relief=tk.FLAT,
        )
        self.entry_loop.pack(side=tk.LEFT, padx=(0, 16))

        tk.Label(r1, text="⏳ NGHỈ GIỮA VÒNG (s):", font=(PIXEL_FONT, 9, "bold"), bg=PIXEL_PANEL, fg=PIXEL_YELLOW).pack(side=tk.LEFT, padx=(0, 4))
        self.entry_delay = tk.Entry(
            r1,
            textvariable=self.loop_delay_var,
            width=5,
            bg="#21243a",
            fg=PIXEL_WHITE,
            insertbackground=PIXEL_CYAN,
            font=(PIXEL_FONT, 9, "bold"),
            relief=tk.FLAT,
        )
        self.entry_delay.pack(side=tk.LEFT, padx=(0, 8))

        # Row 2 Options
        r2 = tk.Frame(cfg_frame, bg=PIXEL_PANEL)
        r2.pack(fill=tk.X, pady=(8, 0))

        chk1 = tk.Checkbutton(
            r2,
            text="✔ BỎ DI CHUỘT RÁC (CHỈ LƯU CLICK & PHÍM - CHUẨN CHO HIS)",
            variable=self.ignore_movement_var,
            font=(PIXEL_FONT, 8, "bold"),
            bg=PIXEL_PANEL,
            fg=PIXEL_CYAN,
            activebackground=PIXEL_PANEL,
            activeforeground=PIXEL_CYAN,
            selectcolor="#21243a",
        )
        chk1.pack(side=tk.LEFT, padx=(0, 16))

        chk2 = tk.Checkbutton(
            r2,
            text="✔ ĐẾM NGƯỢC 3 GIÂY KHI BẤM NÚT TRÊN APP",
            variable=self.countdown_var,
            font=(PIXEL_FONT, 8, "bold"),
            bg=PIXEL_PANEL,
            fg=PIXEL_CYAN,
            activebackground=PIXEL_PANEL,
            activeforeground=PIXEL_CYAN,
            selectcolor="#21243a",
        )
        chk2.pack(side=tk.LEFT)

        # 5. RETRO ACTION LIST (TREEVIEW)
        list_container = tk.Frame(
            self.root,
            bg=PIXEL_PANEL,
            highlightbackground=PIXEL_BORDER,
            highlightthickness=2,
            padx=6,
            pady=6,
        )
        list_container.pack(fill=tk.BOTH, expand=True, padx=14, pady=4)

        list_title = tk.Label(
            list_container,
            text="📜 BẢNG KỊCH BẢN THAO TÁC (ACTION SEQUENCE):",
            font=(PIXEL_FONT, 9, "bold"),
            bg=PIXEL_PANEL,
            fg=PIXEL_PURPLE,
        )
        list_title.pack(anchor="w", padx=4, pady=(2, 4))

        tree_inner = tk.Frame(list_container, bg=PIXEL_PANEL)
        tree_inner.pack(fill=tk.BOTH, expand=True)

        cols = ("stt", "delay", "type", "detail")
        self.tree = ttk.Treeview(
            tree_inner,
            columns=cols,
            show="headings",
            selectmode="browse",
            style="Retro.Treeview",
        )

        self.tree.heading("stt", text="#")
        self.tree.heading("delay", text="CHỜ (s)")
        self.tree.heading("type", text="LOẠI THAO TÁC")
        self.tree.heading("detail", text="CHI TIẾT (TỌA ĐỘ / PHÍM / NÚT BẤM)")

        self.tree.column("stt", width=50, anchor="center")
        self.tree.column("delay", width=90, anchor="center")
        self.tree.column("type", width=140, anchor="center")
        self.tree.column("detail", width=480, anchor="w")

        scroll = ttk.Scrollbar(tree_inner, orient=tk.VERTICAL, command=self.tree.yview, style="Retro.Vertical.TScrollbar")
        self.tree.configure(yscroll=scroll.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # 6. ACTION CONTROLS & STATUS BAR
        bot_bar = tk.Frame(self.root, bg=PIXEL_BG)
        bot_bar.pack(fill=tk.X, padx=14, pady=4)

        self.lbl_stats = tk.Label(
            bot_bar,
            text="[ 📊 THAO TÁC: 000 ]   [ ⏱ TỔNG: 0.0s ]",
            font=(PIXEL_FONT, 9, "bold"),
            bg=PIXEL_BG,
            fg=PIXEL_YELLOW,
        )
        self.lbl_stats.pack(side=tk.LEFT)

        PixelButton(bot_bar, text="🗑 XÓA HẾT", bg_color="#363952", command=self._cmd_clear_actions, padx=6, pady=3).pack(side=tk.RIGHT, padx=(4, 0))
        PixelButton(bot_bar, text="❌ XÓA BƯỚC", bg_color="#363952", command=self._cmd_delete_selected_action, padx=6, pady=3).pack(side=tk.RIGHT, padx=(4, 0))
        PixelButton(bot_bar, text="✏️ SỬA CHỜ", bg_color="#2c5282", command=self._cmd_edit_delay, padx=6, pady=3).pack(side=tk.RIGHT, padx=(4, 0))
        PixelButton(bot_bar, text="💾 LƯU .JSON", bg_color="#1b4965", command=self._cmd_save_file, padx=8, pady=3).pack(side=tk.RIGHT, padx=(4, 0))
        PixelButton(bot_bar, text="📂 MỞ .JSON", bg_color="#2a6f97", command=self._cmd_load_file, padx=8, pady=3).pack(side=tk.RIGHT, padx=(4, 0))

        # 7. RETRO FOOTER TIPS
        footer = tk.Frame(
            self.root,
            bg="#111322",
            highlightbackground=PIXEL_BORDER,
            highlightthickness=1,
            padx=10,
            pady=4,
        )
        footer.pack(fill=tk.X, padx=14, pady=(2, 10))

        tip_lbl = tk.Label(
            footer,
            text="💡 PRO TIP: Bấm [F8] trực tiếp tại màn hình HIS để ghi chuẩn nhất. Trước bước KÝ SỐ, nên dùng '✏️ SỬA CHỜ' tăng thời gian lên 1.5s - 2.0s để máy chủ nạp chứng thư số.",
            font=(PIXEL_FONT, 8),
            bg="#111322",
            fg=PIXEL_MUTED,
            justify="left",
        )
        tip_lbl.pack(anchor="w")

    # ==========================================
    # LOGIC ĐIỀU KHIỂN & CẬP NHẬT TRẠNG THÁI
    # ==========================================
    def _parse_speed(self) -> float:
        raw = self.speed_var.get()
        if "0.5x" in raw:
            return 0.5
        elif "0.8x" in raw:
            return 0.8
        elif "1.25x" in raw:
            return 1.25
        elif "1.5x" in raw:
            return 1.5
        elif "2.0x" in raw:
            return 2.0
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
                bg="#3d2800",
                fg=PIXEL_YELLOW,
                border=PIXEL_YELLOW,
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

    def _set_hud(self, text: str, bg: str, fg: str, border: str):
        self.hud_frame.configure(bg=bg, highlightbackground=border)
        self.hud_status_lbl.configure(text=text, bg=bg, fg=fg)

    def _on_manager_state_changed(self, new_state: str):
        self.root.after(0, lambda: self._handle_state_ui(new_state))

    def _handle_state_ui(self, state: str):
        if state == MacroManager.STATE_IDLE:
            self._set_hud(
                "● STATUS: SẴN SÀNG (READY)   │   [F8] HỌC THAO TÁC   │   [F9] CHẠY BOT   │   [ESC] DỪNG KHẨN CẤP",
                bg="#11291f",
                fg=PIXEL_GREEN,
                border=PIXEL_GREEN,
            )
            self.btn_rec.configure(state=tk.NORMAL)
            self.btn_stop.configure(state=tk.DISABLED, fg=PIXEL_MUTED)
            self.btn_play.configure(state=tk.NORMAL)
            self._refresh_action_tree()

        elif state == MacroManager.STATE_RECORDING:
            self._set_hud(
                "🔴 [REC] ĐANG GHI NHỚ THAO TÁC... HÃY LÀM TRÊN HIS! XONG NHẤN F8 HOẶC ESC ĐỂ LƯU",
                bg="#3a0d18",
                fg=PIXEL_RED,
                border=PIXEL_RED,
            )
            self.btn_rec.configure(state=tk.DISABLED)
            self.btn_stop.configure(state=tk.NORMAL, fg=PIXEL_WHITE)
            self.btn_play.configure(state=tk.DISABLED)

        elif state == MacroManager.STATE_PLAYING:
            self._set_hud(
                "🔵 [RUN] BOT ĐANG TỰ ĐỘNG THỰC THI... NHẤN PHÍM ESC BẤT CỨ LÚC NÀO ĐỂ DỪNG NGAY!",
                bg="#0b2545",
                fg=PIXEL_CYAN,
                border=PIXEL_CYAN,
            )
            self.btn_rec.configure(state=tk.DISABLED)
            self.btn_stop.configure(state=tk.DISABLED, fg=PIXEL_MUTED)
            self.btn_play.configure(state=tk.DISABLED)

    def _on_action_recorded(self, action: MacroAction, count: int):
        self.root.after(0, lambda: self._add_action_to_tree(action, count))

    def _on_player_step(self, step: int, total: int, cur_loop: int, total_loops: int):
        loop_str = f"VÒNG {cur_loop}/{total_loops}" if total_loops > 0 else f"VÒNG {cur_loop} (VÔ HẠN)"
        txt = f"🔵 [RUN] {loop_str} ── BƯỚC {step:02d}/{total:02d} │ NHẤN ESC ĐỂ DỪNG KHẨN CẤP"
        self.root.after(0, lambda: self._set_hud(txt, bg="#0b2545", fg=PIXEL_CYAN, border=PIXEL_CYAN))

    def _on_player_finished(self, success: bool, aborted: bool):
        if aborted:
            msg = "ĐÃ DỪNG KHẨN CẤP THEO LỆNH (ESC)"
            self.root.after(0, lambda: self._set_hud(f"⚠️ {msg} │ [F8] GHI TIẾP │ [F9] CHẠY LẠI", bg="#3d2800", fg=PIXEL_YELLOW, border=PIXEL_YELLOW))
        else:
            msg = "HOÀN TẤT TOÀN BỘ KỊCH BẢN THÀNH CÔNG!"
            self.root.after(0, lambda: self._set_hud(f"⭐ {msg} │ [F8] GHI TIẾP │ [F9] CHẠY LẠI", bg="#11291f", fg=PIXEL_GREEN, border=PIXEL_GREEN))

    # ==========================================
    # QUẢN LÝ BẢNG KỊCH BẢN (TREEVIEW)
    # ==========================================
    def _format_action_display(self, action: MacroAction):
        act_type = action.action_type
        if act_type == "mouse_click":
            st = "DOWN" if action.pressed else "UP"
            btn = (action.button or "left").upper()
            t_name = f"MOUSE {btn} [{st}]"
            detail = f"TỌA ĐỘ: (X={action.x}, Y={action.y})"
        elif act_type == "mouse_move":
            t_name = "MOUSE MOVE"
            detail = f"TỌA ĐỘ: (X={action.x}, Y={action.y})"
        elif act_type == "mouse_scroll":
            t_name = "MOUSE SCROLL"
            detail = f"TẠI ({action.x}, {action.y}) | CUỘN: {action.dy}"
        elif act_type == "key_press":
            t_name = "KEY PRESS"
            detail = f"PHÍM: [{action.key}]"
        elif act_type == "key_release":
            t_name = "KEY RELEASE"
            detail = f"PHÍM: [{action.key}]"
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
        self.lbl_stats.configure(text=f"[ 📊 THAO TÁC: {total:03d} ]   [ ⏱ TỔNG: {total_time:.2f}s ]")

    def _cmd_delete_selected_action(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("THÔNG BÁO", "Hãy bấm chọn một dòng trong bảng để xóa!")
            return
        idx = self.tree.index(selected[0])
        if 0 <= idx < len(self.manager.actions):
            del self.manager.actions[idx]
            self._refresh_action_tree()

    def _cmd_edit_delay(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("THÔNG BÁO", "Hãy bấm chọn một dòng trong bảng để sửa thời gian chờ!")
            return
        idx = self.tree.index(selected[0])
        action = self.manager.actions[idx]

        new_val = simpledialog.askfloat(
            "CHỈNH SỬA ĐỘ TRỄ",
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
