"""Chặn request lạ vào các web UI local (chỉ nghe ở 127.0.0.1 nhưng trình duyệt vẫn gọi tới được).

Một trang web bất kỳ đang mở trong trình duyệt có thể POST tới http://localhost:<port>/api/... (CSRF), hoặc trỏ tên miền
của nó về 127.0.0.1 để đọc luôn kết quả (DNS rebinding). Mỗi server gọi `localguard.ok(self)` ở đầu do_GET / do_POST:
- Host phải là localhost / 127.0.0.1 / [::1]  → chặn DNS rebinding
- Origin (trình duyệt gửi kèm mọi POST và mọi request khác gốc) phải là trang local  → chặn CSRF
Request không có Origin (curl, urllib của bot Telegram, mở trang trực tiếp) vẫn qua như cũ.
"""
from urllib.parse import urlparse

LOCAL = {"localhost", "127.0.0.1", "[::1]", "::1"}


def _host(value: str) -> str:
    value = value.strip().lower()
    if value.startswith("["):                 # [::1]:8760
        return value.split("]")[0] + "]"
    return value.rsplit(":", 1)[0] if ":" in value else value


def allowed(headers, extra_origins=()) -> bool:
    if _host(headers.get("Host", "")) not in LOCAL:
        return False
    origin = headers.get("Origin")
    if origin is None:
        return True
    if origin in extra_origins:
        return True
    u = urlparse(origin)
    return u.scheme in ("http", "https") and (u.hostname or "") in LOCAL


def ok(handler, extra_origins=()) -> bool:
    """True nếu request hợp lệ; không thì đã trả 403 và server phải dừng xử lý."""
    if allowed(handler.headers, extra_origins):
        return True
    handler.close_connection = True           # body POST chưa đọc: không dùng lại kết nối
    handler.send_error(403, "request khong phai tu trang local")
    return False
