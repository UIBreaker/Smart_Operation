"""
Smart Operation - Core Engine (v0.4.1)
Chịu trách nhiệm:
- Ghi và phát lại chuột/bàn phím (DPI Awareness, Emergency Stop).
- Hỗ trợ đa kịch bản (Multi-Script Profiles) với tổ hợp phím riêng cho từng kịch bản.
- Bộ lắng nghe phím tắt toàn cục động (Dynamic GlobalHotKeys).
- Quản lý thư viện kịch bản (Script Library Storage).
"""

import ctypes
import json
import os
import sys
import time
import threading
import uuid
import winsound
from dataclasses import dataclass, asdict, field
from typing import List, Dict, Any, Optional, Callable

from pynput import mouse, keyboard


# ==========================================
# 1. WINDOWS DPI AWARENESS
# ==========================================
def enable_dpi_awareness():
    """Đảm bảo tọa độ chuột (x, y) trên màn hình Windows không bị lệch tỷ lệ DPI scaling (125%, 150%)."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


# ==========================================
# 2. AUDIO FEEDBACK (WINDOWS NATIVE)
# ==========================================
def play_sound(sound_type: str):
    """Phát âm thanh thông báo không chặn luồng (non-blocking)."""
    def _beep():
        try:
            if sound_type == "start_record":
                winsound.Beep(1000, 150)
            elif sound_type == "stop_record":
                winsound.Beep(700, 150)
            elif sound_type == "start_play":
                winsound.Beep(1200, 100)
                winsound.Beep(1500, 100)
            elif sound_type == "stop_play":
                winsound.Beep(1200, 200)
            elif sound_type == "emergency_stop":
                winsound.Beep(500, 300)
        except Exception:
            pass
    threading.Thread(target=_beep, daemon=True).start()


# ==========================================
# 3. HELPER CHUYỂN ĐỔI PHÍM & CHUỘT
# ==========================================
def key_to_str(key: Any) -> str:
    """Chuyển đổi đối tượng pynput Key/KeyCode sang chuỗi lưu trữ JSON."""
    if isinstance(key, keyboard.Key):
        return f"Key.{key.name}"
    elif hasattr(key, "char") and key.char is not None:
        return key.char
    elif hasattr(key, "vk") and key.vk is not None:
        return f"vk_{key.vk}"
    return str(key)


def str_to_key(s: str) -> Any:
    """Khôi phục đối tượng phím từ chuỗi JSON."""
    if s.startswith("Key."):
        name = s.split(".", 1)[1]
        return getattr(keyboard.Key, name, None)
    elif s.startswith("vk_"):
        vk = int(s.split("_", 1)[1])
        return keyboard.KeyCode.from_vk(vk)
    return keyboard.KeyCode.from_char(s)


def button_to_str(button: mouse.Button) -> str:
    return button.name if hasattr(button, "name") else str(button)


def str_to_button(s: str) -> mouse.Button:
    return getattr(mouse.Button, s, mouse.Button.left)


def normalize_hotkey(hk_str: str) -> str:
    """
    Chuyển đổi chuỗi tổ hợp phím thân thiện (VD: 'F9', 'Ctrl+F1', 'Alt+1', 'Ctrl+Shift+K', 'ESC')
    sang định dạng chuẩn của pynput.keyboard.GlobalHotKeys (VD: '<f9>', '<ctrl>+<f1>', '<alt>+1', '<esc>').
    """
    if not hk_str:
        return ""
    hk = hk_str.lower().strip()
    parts = [p.strip() for p in hk.split("+") if p.strip()]
    pynput_parts = []
    for p in parts:
        if p in ("ctrl", "control"):
            pynput_parts.append("<ctrl>")
        elif p in ("alt",):
            pynput_parts.append("<alt>")
        elif p in ("shift",):
            pynput_parts.append("<shift>")
        elif p.startswith("f") and p[1:].isdigit():
            pynput_parts.append(f"<{p}>")
        elif p in ("esc", "escape"):
            pynput_parts.append("<esc>")
        elif p in ("enter", "tab", "space", "home", "end", "page_up", "page_down"):
            pynput_parts.append(f"<{p}>")
        else:
            pynput_parts.append(p)
    return "+".join(pynput_parts)


# ==========================================
# 4. DATA MODEL CHO MỖI THAO TÁC & KỊCH BẢN
# ==========================================
@dataclass
class MacroAction:
    action_type: str       # 'mouse_click', 'mouse_move', 'mouse_scroll', 'key_press', 'key_release'
    delay: float           # Thời gian chờ so với thao tác trước (giây)
    x: Optional[int] = None
    y: Optional[int] = None
    button: Optional[str] = None     # 'left', 'right', 'middle'
    pressed: Optional[bool] = None   # True = nhấn xuống, False = nhả ra
    dx: Optional[int] = None
    dy: Optional[int] = None
    key: Optional[str] = None        # Tên phím (Key.enter, 'a', ...)

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MacroAction":
        return cls(
            action_type=data.get("action_type", ""),
            delay=float(data.get("delay", 0.0)),
            x=data.get("x"),
            y=data.get("y"),
            button=data.get("button"),
            pressed=data.get("pressed"),
            dx=data.get("dx"),
            dy=data.get("dy"),
            key=data.get("key"),
        )


@dataclass
class ScriptProfile:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Kịch bản mới"
    hotkey: str = "F9"
    actions: List[MacroAction] = field(default_factory=list)
    speed: float = 1.0
    loop_count: int = 1
    loop_delay: float = 1.0
    enabled: bool = True
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "hotkey": self.hotkey,
            "speed": self.speed,
            "loop_count": self.loop_count,
            "loop_delay": self.loop_delay,
            "enabled": self.enabled,
            "description": self.description,
            "total_actions": len(self.actions),
            "actions": [act.to_dict() for act in self.actions],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScriptProfile":
        raw_actions = data.get("actions", [])
        actions = [MacroAction.from_dict(item) for item in raw_actions]
        return cls(
            id=data.get("id", str(uuid.uuid4())[:8]),
            name=data.get("name", "Kịch bản mới"),
            hotkey=data.get("hotkey", "F9"),
            actions=actions,
            speed=float(data.get("speed", 1.0)),
            loop_count=int(data.get("loop_count", 1)),
            loop_delay=float(data.get("loop_delay", 1.0)),
            enabled=data.get("enabled", True),
            description=data.get("description", ""),
        )


# ==========================================
# 5. RECORDER: BỘ GHI NHỚ THAO TÁC
# ==========================================
class MacroRecorder:
    def __init__(self, record_movement: bool = False):
        self.record_movement = record_movement
        self.actions: List[MacroAction] = []
        self.is_recording = False
        self._last_time = 0.0
        self._lock = threading.Lock()

        # Listeners
        self._mouse_listener: Optional[mouse.Listener] = None
        self._keyboard_listener: Optional[keyboard.Listener] = None

        # Phím điều khiển mặc định
        self.hotkey_record_key = keyboard.Key.f8
        self.hotkey_stop_key = keyboard.Key.esc

        # Callback khi có action mới
        self.on_action_recorded: Optional[Callable[[MacroAction, int], None]] = None

    def _get_delay(self) -> float:
        now = time.perf_counter()
        if self._last_time == 0.0:
            delay = 0.0
        else:
            delay = max(0.001, round(now - self._last_time, 4))
        self._last_time = now
        return delay

    def _add_action(self, action: MacroAction):
        with self._lock:
            if not self.is_recording:
                return
            self.actions.append(action)
            count = len(self.actions)

        if self.on_action_recorded:
            self.on_action_recorded(action, count)

    def _on_mouse_click(self, x: int, y: int, button: mouse.Button, pressed: bool):
        if not self.is_recording:
            return
        delay = self._get_delay()
        action = MacroAction(
            action_type="mouse_click",
            delay=delay,
            x=int(x),
            y=int(y),
            button=button_to_str(button),
            pressed=pressed,
        )
        self._add_action(action)

    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int):
        if not self.is_recording:
            return
        delay = self._get_delay()
        action = MacroAction(
            action_type="mouse_scroll",
            delay=delay,
            x=int(x),
            y=int(y),
            dx=int(dx),
            dy=int(dy),
        )
        self._add_action(action)

    def _on_mouse_move(self, x: int, y: int):
        if not self.is_recording or not self.record_movement:
            return
        now = time.perf_counter()
        if now - self._last_time < 0.03:
            return
        delay = self._get_delay()
        action = MacroAction(
            action_type="mouse_move",
            delay=delay,
            x=int(x),
            y=int(y),
        )
        self._add_action(action)

    def _on_key_press(self, key: Any):
        if not self.is_recording:
            return
        if key in (self.hotkey_record_key, self.hotkey_stop_key):
            return
        delay = self._get_delay()
        action = MacroAction(
            action_type="key_press",
            delay=delay,
            key=key_to_str(key),
        )
        self._add_action(action)

    def _on_key_release(self, key: Any):
        if not self.is_recording:
            return
        if key in (self.hotkey_record_key, self.hotkey_stop_key):
            return
        delay = self._get_delay()
        action = MacroAction(
            action_type="key_release",
            delay=delay,
            key=key_to_str(key),
        )
        self._add_action(action)

    def start(self):
        with self._lock:
            self.actions = []
            self.is_recording = True
            self._last_time = time.perf_counter()

        play_sound("start_record")

        self._mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll,
            on_move=self._on_mouse_move,
        )
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._mouse_listener.daemon = True
        self._keyboard_listener.daemon = True
        self._mouse_listener.start()
        self._keyboard_listener.start()

    def stop(self) -> List[MacroAction]:
        with self._lock:
            self.is_recording = False

        if self._mouse_listener:
            try:
                self._mouse_listener.stop()
            except Exception:
                pass
            self._mouse_listener = None

        if self._keyboard_listener:
            try:
                self._keyboard_listener.stop()
            except Exception:
                pass
            self._keyboard_listener = None

        play_sound("stop_record")
        return list(self.actions)


# ==========================================
# 6. PLAYER: BỘ THỰC HIỆN THAO TÁC (REPLAY)
# ==========================================
class MacroPlayer:
    def __init__(self):
        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()
        self.is_playing = False
        self._abort_event = threading.Event()
        self._play_thread: Optional[threading.Thread] = None

        # Callbacks
        self.on_step: Optional[Callable[[int, int, int, int], None]] = None
        self.on_finished: Optional[Callable[[bool, bool], None]] = None

    def is_running(self) -> bool:
        return self.is_playing

    def stop(self):
        """Dừng khẩn cấp ngay lập tức."""
        if not self.is_playing:
            return
        self._abort_event.set()
        play_sound("emergency_stop")
        self._release_all_modifiers()

    def _release_all_modifiers(self):
        try:
            for btn in (mouse.Button.left, mouse.Button.right, mouse.Button.middle):
                self.mouse_controller.release(btn)
        except Exception:
            pass

        modifier_keys = [
            keyboard.Key.ctrl_l, keyboard.Key.ctrl_r,
            keyboard.Key.alt_l, keyboard.Key.alt_r,
            keyboard.Key.shift_l, keyboard.Key.shift_r,
        ]
        for k in modifier_keys:
            try:
                self.keyboard_controller.release(k)
            except Exception:
                pass

    def play_async(
        self,
        actions: List[MacroAction],
        speed: float = 1.0,
        loop_count: int = 1,
        loop_delay: float = 1.0,
    ):
        if self.is_playing:
            return
        self._abort_event.clear()
        self.is_playing = True
        self._play_thread = threading.Thread(
            target=self._run_playback,
            args=(actions, speed, loop_count, loop_delay),
            daemon=True,
        )
        self._play_thread.start()

    def _run_playback(
        self,
        actions: List[MacroAction],
        speed: float,
        loop_count: int,
        loop_delay: float,
    ):
        total_steps = len(actions)
        speed = max(0.1, speed)
        current_loop = 1
        aborted = False

        play_sound("start_play")

        try:
            while not self._abort_event.is_set():
                for idx, action in enumerate(actions, start=1):
                    if self._abort_event.is_set():
                        aborted = True
                        break

                    actual_delay = action.delay / speed
                    if actual_delay > 0:
                        if self._abort_event.wait(actual_delay):
                            aborted = True
                            break

                    self._execute_action(action)

                    if self.on_step:
                        self.on_step(idx, total_steps, current_loop, loop_count)

                if aborted:
                    break

                if loop_count > 0 and current_loop >= loop_count:
                    break

                current_loop += 1
                if loop_delay > 0:
                    if self._abort_event.wait(loop_delay):
                        aborted = True
                        break

        except Exception as ex:
            print(f"Lỗi khi thực hiện thao tác: {ex}", file=sys.stderr)
            aborted = True
        finally:
            self._release_all_modifiers()
            self.is_playing = False
            if not aborted:
                play_sound("stop_play")
            if self.on_finished:
                self.on_finished(not aborted, aborted)

    def _execute_action(self, action: MacroAction):
        act_type = action.action_type

        if act_type == "mouse_click":
            if action.x is not None and action.y is not None:
                self.mouse_controller.position = (action.x, action.y)
            btn = str_to_button(action.button or "left")
            if action.pressed:
                self.mouse_controller.press(btn)
            else:
                self.mouse_controller.release(btn)

        elif act_type == "mouse_move":
            if action.x is not None and action.y is not None:
                self.mouse_controller.position = (action.x, action.y)

        elif act_type == "mouse_scroll":
            if action.x is not None and action.y is not None:
                self.mouse_controller.position = (action.x, action.y)
            dx = action.dx or 0
            dy = action.dy or 0
            self.mouse_controller.scroll(dx, dy)

        elif act_type == "key_press":
            if action.key:
                k = str_to_key(action.key)
                if k is not None:
                    self.keyboard_controller.press(k)

        elif act_type == "key_release":
            if action.key:
                k = str_to_key(action.key)
                if k is not None:
                    self.keyboard_controller.release(k)


# ==========================================
# 7. SCRIPT LIBRARY & STORAGE
# ==========================================
class MacroStorage:
    @staticmethod
    def save_to_file(actions: List[MacroAction], file_path: str, metadata: Optional[Dict[str, Any]] = None):
        payload = {
            "version": "1.0",
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "metadata": metadata or {},
            "total_actions": len(actions),
            "actions": [act.to_dict() for act in actions],
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_from_file(file_path: str) -> List[MacroAction]:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_actions = data.get("actions", [])
        return [MacroAction.from_dict(item) for item in raw_actions]

    @staticmethod
    def save_library(profiles: List[ScriptProfile], file_path: str, settings: Optional[Dict[str, Any]] = None):
        """Lưu toàn bộ thư viện nhiều kịch bản ra file JSON."""
        payload = {
            "version": "0.4.1",
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "settings": settings or {},
            "profiles": [p.to_dict() for p in profiles],
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    @staticmethod
    def load_library(file_path: str) -> tuple[List[ScriptProfile], Dict[str, Any]]:
        """Nạp thư viện nhiều kịch bản từ file JSON."""
        if not os.path.isfile(file_path):
            return [], {}
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        raw_profiles = data.get("profiles", [])
        profiles = [ScriptProfile.from_dict(item) for item in raw_profiles]
        settings = data.get("settings", {})
        return profiles, settings


# ==========================================
# 8. MACRO MANAGER: QUẢN LÝ ĐA KỊCH BẢN & PHÍM TẮT TOÀN CỤC
# ==========================================
class MacroManager:
    STATE_IDLE = "idle"
    STATE_RECORDING = "recording"
    STATE_PLAYING = "playing"

    def __init__(self, library_path: str = "scripts_library.json"):
        self.state = self.STATE_IDLE
        self.recorder = MacroRecorder(record_movement=False)
        self.player = MacroPlayer()

        self.library_path = library_path
        self.profiles: List[ScriptProfile] = []
        self.active_profile_id: Optional[str] = None

        # Cài đặt phím tắt hệ thống
        self.hotkey_record_str = "F8"
        self.hotkey_panic_str = "ESC"

        # Cài đặt ứng dụng
        self.minimize_to_tray_on_close = True

        # Global HotKeys Listener
        self._global_hotkeys: Optional[keyboard.GlobalHotKeys] = None
        self._lock = threading.Lock()

        # Callbacks cập nhật UI
        self.on_state_changed: Optional[Callable[[str], None]] = None
        self.on_action_recorded: Optional[Callable[[MacroAction, int], None]] = None
        self.on_step: Optional[Callable[[int, int, int, int], None]] = None
        self.on_play_finished: Optional[Callable[[bool, bool], None]] = None
        self.on_profile_triggered: Optional[Callable[[ScriptProfile], None]] = None

        self.recorder.on_action_recorded = self._handle_action_recorded
        self.player.on_step = self._handle_step
        self.player.on_finished = self._handle_play_finished

        # Tải thư viện kịch bản đã lưu
        self.load_library()

    def get_active_profile(self) -> Optional[ScriptProfile]:
        if not self.profiles:
            return None
        if self.active_profile_id:
            for p in self.profiles:
                if p.id == self.active_profile_id:
                    return p
        return self.profiles[0]

    def set_active_profile(self, profile_id: str):
        self.active_profile_id = profile_id

    def load_library(self):
        loaded_profiles, settings = MacroStorage.load_library(self.library_path)
        if loaded_profiles:
            self.profiles = loaded_profiles
            self.active_profile_id = self.profiles[0].id
        else:
            # Tạo sẵn 1 kịch bản mẫu mặc định cho người dùng HIS
            sample_profile = ScriptProfile(
                id="default_kiso",
                name="Ký số & Kết thúc khám",
                hotkey="F9",
                actions=[
                    MacroAction("mouse_click", delay=0.5, x=420, y=310, button="left", pressed=True),
                    MacroAction("mouse_click", delay=0.05, x=420, y=310, button="left", pressed=False),
                    MacroAction("mouse_click", delay=0.8, x=860, y=620, button="left", pressed=True),
                    MacroAction("mouse_click", delay=0.05, x=860, y=620, button="left", pressed=False),
                    MacroAction("mouse_click", delay=1.5, x=980, y=720, button="left", pressed=True),
                    MacroAction("mouse_click", delay=0.05, x=980, y=720, button="left", pressed=False),
                ],
                speed=1.0,
                loop_count=1,
                loop_delay=1.0,
                description="Kịch bản tự động hóa ký số và hoàn tất khám bệnh",
            )
            self.profiles = [sample_profile]
            self.active_profile_id = sample_profile.id

        if settings:
            self.hotkey_record_str = settings.get("hotkey_record", "F8")
            self.hotkey_panic_str = settings.get("hotkey_panic", "ESC")
            self.minimize_to_tray_on_close = settings.get("minimize_to_tray_on_close", True)

    def save_library(self):
        settings = {
            "hotkey_record": self.hotkey_record_str,
            "hotkey_panic": self.hotkey_panic_str,
            "minimize_to_tray_on_close": self.minimize_to_tray_on_close,
        }
        MacroStorage.save_library(self.profiles, self.library_path, settings=settings)

    def _set_state(self, new_state: str):
        with self._lock:
            self.state = new_state
        if self.on_state_changed:
            self.on_state_changed(new_state)

    # ------------------------------------------
    # QUẢN LÝ HOTKEYS TOÀN CỤC (GLOBAL HOTKEYS)
    # ------------------------------------------
    def start_global_hotkeys(self):
        """Khởi động bộ lắng nghe phím tắt toàn hệ thống cho tất cả kịch bản."""
        self.stop_global_hotkeys()

        hotkey_map = {}

        # 1. Phím tắt Bắt đầu / Dừng học thao tác
        norm_rec = normalize_hotkey(self.hotkey_record_str)
        if norm_rec:
            hotkey_map[norm_rec] = self._on_hotkey_toggle_record

        # 2. Phím tắt Dừng khẩn cấp
        norm_panic = normalize_hotkey(self.hotkey_panic_str)
        if norm_panic:
            hotkey_map[norm_panic] = self.stop_playing

        # 3. Phím tắt riêng cho TỪNG kịch bản được kích hoạt (Enabled)
        for profile in self.profiles:
            if not profile.enabled or not profile.actions:
                continue
            norm_hk = normalize_hotkey(profile.hotkey)
            if norm_hk and norm_hk not in hotkey_map:
                # Đóng gói profile vào callback
                hotkey_map[norm_hk] = (lambda p=profile: self._on_hotkey_play_profile(p))

        try:
            self._global_hotkeys = keyboard.GlobalHotKeys(hotkey_map)
            self._global_hotkeys.daemon = True
            self._global_hotkeys.start()
        except Exception as ex:
            print(f"Lỗi khởi động GlobalHotKeys: {ex}", file=sys.stderr)

    def stop_global_hotkeys(self):
        if self._global_hotkeys:
            try:
                self._global_hotkeys.stop()
            except Exception:
                pass
            self._global_hotkeys = None

    def reload_global_hotkeys(self):
        """Cập nhật lại phím tắt khi người dùng thêm/sửa kịch bản hoặc đổi cài đặt."""
        self.start_global_hotkeys()

    def _on_hotkey_toggle_record(self):
        if self.state == self.STATE_IDLE:
            self.start_recording()
        elif self.state == self.STATE_RECORDING:
            self.stop_recording()

    def _on_hotkey_play_profile(self, profile: ScriptProfile):
        if self.state == self.STATE_IDLE:
            self.set_active_profile(profile.id)
            if self.on_profile_triggered:
                self.on_profile_triggered(profile)
            self.start_playing_profile(profile)

    # ------------------------------------------
    # GHI & PHÁT KỊCH BẢN
    # ------------------------------------------
    def start_recording(self, record_movement: bool = False):
        if self.state != self.STATE_IDLE:
            return
        self.recorder.record_movement = record_movement
        self.recorder.start()
        self._set_state(self.STATE_RECORDING)

    def stop_recording(self) -> List[MacroAction]:
        if self.state != self.STATE_RECORDING:
            return []
        recorded = self.recorder.stop()
        self._set_state(self.STATE_IDLE)
        # Tự động gán vào profile hiện tại hoặc trả về
        active = self.get_active_profile()
        if active:
            active.actions = recorded
            self.save_library()
        self.reload_global_hotkeys()
        return recorded

    def start_playing_profile(self, profile: ScriptProfile):
        if self.state != self.STATE_IDLE or not profile.actions:
            return
        self._set_state(self.STATE_PLAYING)
        self.player.play_async(
            profile.actions,
            speed=profile.speed,
            loop_count=profile.loop_count,
            loop_delay=profile.loop_delay,
        )

    def start_playing_active(self):
        active = self.get_active_profile()
        if active:
            self.start_playing_profile(active)

    def stop_playing(self):
        if self.state == self.STATE_PLAYING:
            self.player.stop()
        elif self.state == self.STATE_RECORDING:
            self.stop_recording()

    def _handle_action_recorded(self, action: MacroAction, count: int):
        if self.on_action_recorded:
            self.on_action_recorded(action, count)

    def _handle_step(self, step: int, total: int, cur_loop: int, total_loops: int):
        if self.on_step:
            self.on_step(step, total, cur_loop, total_loops)

    def _handle_play_finished(self, success: bool, aborted: bool):
        self._set_state(self.STATE_IDLE)
        if self.on_play_finished:
            self.on_play_finished(success, aborted)
