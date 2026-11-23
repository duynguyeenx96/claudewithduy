-- D1: wrangler d1 execute claudewithduy-shop --remote --file worker/schema.sql
CREATE TABLE IF NOT EXISTS orders (
  code TEXT PRIMARY KEY,          -- CWD + 6 ký tự, nằm trong nội dung chuyển khoản
  pack TEXT NOT NULL,
  amount INTEGER NOT NULL,
  email TEXT,
  status TEXT NOT NULL DEFAULT 'pending',  -- pending | paid (đã nhận tiền, chờ giao tay) | delivered
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
