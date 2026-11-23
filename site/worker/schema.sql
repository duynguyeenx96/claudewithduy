-- D1: wrangler d1 execute claudewithduy-shop --remote --file worker/schema.sql
CREATE TABLE IF NOT EXISTS orders (
  code TEXT PRIMARY KEY,          -- CWD + 6 ký tự, nằm trong nội dung chuyển khoản
  pack TEXT NOT NULL,
  amount INTEGER NOT NULL,
  email TEXT,
  secret TEXT,                    -- trả cho trang thanh toán; chỉ ai có nó mới thấy link tải
  status TEXT NOT NULL DEFAULT 'pending',  -- pending | paid (đã nhận tiền) | delivered (đã gửi email)
  note TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  paid_at TEXT,
  delivered_at TEXT
);
-- Mọi giao dịch SePay báo về; id là id giao dịch của SePay nên webhook gửi lặp không xử lý hai lần.
-- code = NULL: không khớp đơn nào, xem tay.
CREATE TABLE IF NOT EXISTS payments (
  id INTEGER PRIMARY KEY,
  code TEXT,
  amount INTEGER,
  content TEXT,
  raw TEXT,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
-- Link tải: hết hạn sau 7 ngày, tối đa 5 lượt. Gửi lại link = thêm dòng mới cho cùng đơn.
CREATE TABLE IF NOT EXISTS downloads (
  token TEXT PRIMARY KEY,
  code TEXT NOT NULL,
  expires_at TEXT NOT NULL,
  uses INTEGER NOT NULL DEFAULT 0,
  max_uses INTEGER NOT NULL DEFAULT 5
);
