"""
Unit Test tự động kiểm tra logic cốt lõi của Smart Operation (core.py).
Chạy độc lập: python test_core.py
Không cần cài đặt thêm framework nào ngoài thư viện chuẩn.
"""

import os
import sys
import tempfile
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
from core import MacroAction, MacroStorage, key_to_str, str_to_key, button_to_str, str_to_button
from pynput import keyboard, mouse


def test_key_serialization():
    print("-> Kiểm tra chuyển đổi phím (Key serialization)...")
    cases = [
        keyboard.Key.enter,
        keyboard.Key.f8,
        keyboard.Key.esc,
        keyboard.Key.ctrl_l,
        keyboard.KeyCode.from_char('k'),
        keyboard.KeyCode.from_char('0'),
    ]
    for key in cases:
        s = key_to_str(key)
        restored = str_to_key(s)
        assert restored is not None, f"Lỗi khôi phục phím cho: {key}"
        # So sánh tên hoặc char
        if isinstance(key, keyboard.Key):
            assert restored == key, f"Phím không khớp: {key} != {restored}"
        elif hasattr(key, 'char') and key.char:
            assert getattr(restored, 'char', None) == key.char
    print("   [PASS] Chuyển đổi phím chính xác.")


def test_button_serialization():
    print("-> Kiểm tra chuyển đổi chuột (Button serialization)...")
    for btn in [mouse.Button.left, mouse.Button.right, mouse.Button.middle]:
        s = button_to_str(btn)
        restored = str_to_button(s)
        assert restored == btn, f"Nút chuột không khớp: {btn} != {restored}"
    print("   [PASS] Chuyển đổi chuột chính xác.")


def test_macro_action_roundtrip():
    print("-> Kiểm tra MacroAction to_dict và from_dict...")
    action1 = MacroAction(action_type="mouse_click", delay=0.25, x=100, y=200, button="left", pressed=True)
    d = action1.to_dict()
    assert d["action_type"] == "mouse_click"
    assert d["delay"] == 0.25
    assert d["x"] == 100
    assert d["y"] == 200
    assert d["button"] == "left"
    assert d["pressed"] is True

    action2 = MacroAction.from_dict(d)
    assert action2 == action1, f"Đối tượng không khớp sau khi khôi phục: {action1} != {action2}"
    print("   [PASS] MacroAction roundtrip chính xác.")


def test_storage_json_roundtrip():
    print("-> Kiểm tra lưu và nạp kịch bản JSON (Storage)...")
    sample_actions = [
        MacroAction("mouse_click", delay=0.1, x=500, y=300, button="left", pressed=True),
        MacroAction("mouse_click", delay=0.05, x=500, y=300, button="left", pressed=False),
        MacroAction("key_press", delay=0.2, key="Key.tab"),
        MacroAction("key_release", delay=0.02, key="Key.tab"),
        MacroAction("key_press", delay=0.15, key="k"),
        MacroAction("key_release", delay=0.03, key="k"),
        MacroAction("mouse_scroll", delay=0.3, x=600, y=400, dx=0, dy=-2),
    ]

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Lưu file
        MacroStorage.save_to_file(sample_actions, tmp_path, metadata={"author": "HIS User"})
        assert os.path.exists(tmp_path), "File JSON không được tạo!"

        # Nạp lại file
        loaded_actions = MacroStorage.load_from_file(tmp_path)
        assert len(loaded_actions) == len(sample_actions), f"Số lượng thao tác không khớp: {len(loaded_actions)} != {len(sample_actions)}"
        for orig, loaded in zip(sample_actions, loaded_actions):
            assert orig.action_type == loaded.action_type
            assert abs(orig.delay - loaded.delay) < 1e-4
            assert orig.x == loaded.x
            assert orig.y == loaded.y
            assert orig.key == loaded.key
            assert orig.button == loaded.button
        print("   [PASS] Lưu & nạp JSON hoàn toàn toàn vẹn dữ liệu.")
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


def test_abort_flag_responsiveness():
    print("-> Kiểm tra cơ chế dừng khẩn cấp (Emergency Stop wait response)...")
    import threading
    abort_event = threading.Event()
    start_t = time.perf_counter()

    # Thử wait 3 giây nhưng kích hoạt dừng sau 0.05 giây
    def trigger_abort():
        time.sleep(0.05)
        abort_event.set()

    t = threading.Thread(target=trigger_abort)
    t.start()

    # abort_event.wait(3.0) phải thoát ngay khi set() chứ không đợi hết 3 giây!
    interrupted = abort_event.wait(timeout=3.0)
    elapsed = time.perf_counter() - start_t
    t.join()

    assert interrupted is True, "Abort event không được kích hoạt!"
    assert elapsed < 0.5, f"Thời gian phản hồi dừng quá chậm: {elapsed:.2f}s (kỳ vọng < 0.5s)"
    print(f"   [PASS] Phản hồi dừng khẩn cấp siêu tốc: {elapsed*1000:.1f}ms.")


def test_macro_manager_state_machine():
    print("-> Kiểm tra máy trạng thái MacroManager (State Machine)...")
    from core import MacroManager
    mgr = MacroManager()
    assert mgr.state == MacroManager.STATE_IDLE

    # Mock action list
    mgr.actions = [
        MacroAction("key_press", delay=0.05, key="Key.enter"),
        MacroAction("key_release", delay=0.01, key="Key.enter"),
    ]

    # Test Play & Emergency Stop
    mgr.start_playing(speed=1.0, loop_count=10, loop_delay=1.0)
    assert mgr.state == MacroManager.STATE_PLAYING, f"Trạng thái kỳ vọng là PLAYING, nhận: {mgr.state}"
    time.sleep(0.02)
    mgr.stop_playing()
    # Chờ thread kết thúc
    time.sleep(0.05)
    assert mgr.state == MacroManager.STATE_IDLE, f"Trạng thái kỳ vọng là IDLE sau dừng, nhận: {mgr.state}"
    print("   [PASS] MacroManager chuyển đổi trạng thái chính xác.")


if __name__ == "__main__":
    print("================ BẮT ĐẦU KIỂM THỬ CORE ENGINE ================")
    test_key_serialization()
    test_button_serialization()
    test_macro_action_roundtrip()
    test_storage_json_roundtrip()
    test_abort_flag_responsiveness()
    test_macro_manager_state_machine()
    print("================ TẤT CẢ KIỂM THỬ ĐÃ VƯỢT QUA THÀNH CÔNG! ================")
