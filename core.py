"""
Smart Operation - Core Engine
Chịu trách nhiệm ghi (Record) và phát lại (Replay) chuột, bàn phím với Windows API & pynput.
Hỗ trợ DPI Awareness, Emergency Stop (ESC), gán phím tắt F8/F9.
"""

import ctypes
import json
import os
import sys
import time
import threading
import winsound
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Callable

from pynput import mouse, keyboard


# ==========================================
# 1. WINDOWS DPI AWARENESS
# ==========================================
def enable_dpi_awareness():
    """Đảm bảo tọa độ chuột (x, y) trên màn hình Windows không bị lệch tỷ lệ DPI scaling (125%, 150%)."""
    try:
        # Per-monitor DPI aware (Windows 8.1+)
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            # System DPI aware fallback
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
    """Chuyển nút chuột thành chuỗi (left, right, middle)."""
    return button.name if hasattr(button, "name") else str(button)


def str_to_button(s: str) -> mouse.Button:
    """Khôi phục nút chuột từ chuỗi."""
    return getattr(mouse.Button, s, mouse.Button.left)


# ==========================================
# 4. DATA MODEL CHO MỖI THAO TÁC
# ==========================================
@dataclass
class MacroAction:
    action_type: str       # 'mouse_click', 'mouse_move', 'mouse_scroll', 'key_press', 'key_release'
    delay: float           # Thời gian chờ so với thao tác trước (giây)
    x: Optional[int] = None
    y: Optional[int] = None
    button: Optional[str] = None     # 'left', 'right', 'middle'
    pressed: Optional[bool] = None   # True = nhấn xuống, False = nhả ra
    dx: Optional[int] = None         # Cuộn chuột ngang
    dy: Optional[int] = None         # Cuộn chuột dọc
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
        self.hotkey_record = keyboard.Key.f8
        self.hotkey_stop = keyboard.Key.esc

        # Callback khi có action mới để cập nhật UI
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
        # Giới hạn tần số ghi di chuyển để tránh hàng ngàn event rác
        now = time.perf_counter()
        if now - self._last_time < 0.03:  # Tối đa ~30 events/giây khi di chuột
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
        # Bỏ qua phím F8 hoặc ESC nếu dùng để dừng ghi
        if key in (self.hotkey_record, self.hotkey_stop):
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
        if key in (self.hotkey_record, self.hotkey_stop):
            return
        delay = self._get_delay()
        action = MacroAction(
            action_type="key_release",
            delay=delay,
            key=key_to_str(key),
        )
        self._add_action(action)

    def start(self):
        """Bắt đầu ghi lại thao tác."""
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
        """Dừng ghi lại và trả về danh sách thao tác đã ghi."""
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
        self.on_finished: Optional[Callable[[bool, bool], None]] = None  # (success, aborted)

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
        """Nhả toàn bộ phím và nút chuột đang giữ để tránh kẹt trạng thái trên Windows."""
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
        """Khởi chạy phát lại trên luồng nền (background thread)."""
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

                    # Tính toán độ trễ theo tốc độ
                    actual_delay = action.delay / speed
                    if actual_delay > 0:
                        # Dùng abort_event.wait thay cho time.sleep để phản hồi phím ESC ngay lập tức
                        if self._abort_event.wait(actual_delay):
                            aborted = True
                            break

                    self._execute_action(action)

                    if self.on_step:
                        self.on_step(idx, total_steps, current_loop, loop_count)

                if aborted:
                    break

                # Kiểm tra số lần lặp lại (0 nghĩa là vô hạn)
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
# 7. LƯU & NẠP KỊCH BẢN (STORAGE)
# ==========================================
class MacroStorage:
    @staticmethod
    def save_to_file(actions: List[MacroAction], file_path: str, metadata: Optional[Dict[str, Any]] = None):
        """Lưu danh sách thao tác ra file JSON chuẩn."""
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
        """Nạp danh sách thao tác từ file JSON."""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Không tìm thấy file: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        raw_actions = data.get("actions", [])
        return [MacroAction.from_dict(item) for item in raw_actions]


# ==========================================
# 8. MACRO MANAGER: ĐIỀU PHỐI TỔNG THỂ & PHÍM TẮT TOÀN CỤC
# ==========================================
class MacroManager:
    STATE_IDLE = "idle"
    STATE_RECORDING = "recording"
    STATE_PLAYING = "playing"

    def __init__(self):
        self.state = self.STATE_IDLE
        self.recorder = MacroRecorder(record_movement=False)
        self.player = MacroPlayer()
        self.actions: List[MacroAction] = []

        # Phím tắt toàn cục
        self.hotkey_record = keyboard.Key.f8
        self.hotkey_play = keyboard.Key.f9
        self.hotkey_stop = keyboard.Key.esc

        # Global listener cho phím tắt khi không ở trong app
        self._global_listener: Optional[keyboard.Listener] = None
        self._lock = threading.Lock()

        # Callbacks cập nhật trạng thái ra ngoài (UI)
        self.on_state_changed: Optional[Callable[[str], None]] = None
        self.on_action_recorded: Optional[Callable[[MacroAction, int], None]] = None
        self.on_step: Optional[Callable[[int, int, int, int], None]] = None
        self.on_play_finished: Optional[Callable[[bool, bool], None]] = None

        self.recorder.on_action_recorded = self._handle_action_recorded
        self.player.on_step = self._handle_step
        self.player.on_finished = self._handle_play_finished

    def start_global_hotkeys(self):
        """Khởi động bộ lắng nghe phím tắt toàn hệ thống Windows."""
        if self._global_listener is None:
            self._global_listener = keyboard.Listener(
                on_press=self._on_global_key_press,
                on_release=self._on_global_key_release,
            )
            self._global_listener.daemon = True
            self._global_listener.start()

    def stop_global_hotkeys(self):
        """Dừng bộ lắng nghe phím tắt."""
        if self._global_listener:
            try:
                self._global_listener.stop()
            except Exception:
                pass
            self._global_listener = None

    def _set_state(self, new_state: str):
        with self._lock:
            self.state = new_state
        if self.on_state_changed:
            self.on_state_changed(new_state)

    def _on_global_key_press(self, key: Any):
        # 1. Dừng khẩn cấp bằng phím ESC bất cứ khi nào
        if key == self.hotkey_stop:
            if self.state == self.STATE_PLAYING:
                self.stop_playing()
                return
            elif self.state == self.STATE_RECORDING:
                self.stop_recording()
                return

        # 2. Phím F8: Bật / Tắt ghi thao tác
        if key == self.hotkey_record:
            if self.state == self.STATE_IDLE:
                self.start_recording()
                return
            elif self.state == self.STATE_RECORDING:
                self.stop_recording()
                return

        # 3. Phím F9: Chạy kịch bản
        if key == self.hotkey_play:
            if self.state == self.STATE_IDLE and self.actions:
                self.start_playing()
                return

    def _on_global_key_release(self, key: Any):
        pass

    def start_recording(self, record_movement: bool = False):
        if self.state != self.STATE_IDLE:
            return
        self.recorder.record_movement = record_movement
        self.recorder.start()
        self._set_state(self.STATE_RECORDING)

    def stop_recording(self) -> List[MacroAction]:
        if self.state != self.STATE_RECORDING:
            return self.actions
        recorded = self.recorder.stop()
        self.actions = recorded
        self._set_state(self.STATE_IDLE)
        return self.actions

    def start_playing(self, speed: float = 1.0, loop_count: int = 1, loop_delay: float = 1.0):
        if self.state != self.STATE_IDLE or not self.actions:
            return
        self._set_state(self.STATE_PLAYING)
        self.player.play_async(self.actions, speed=speed, loop_count=loop_count, loop_delay=loop_delay)

    def stop_playing(self):
        if self.state != self.STATE_PLAYING:
            return
        self.player.stop()

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

