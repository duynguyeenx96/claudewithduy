// Worker của site: /api/* xử lý ở đây, còn lại trả file tĩnh trong dist.
//   POST /api/order        {pack, email}          -> tạo đơn + QR (chỉ khi SALES_OPEN = "1" và gói có giá)
//   GET  /api/order/:code                          -> trạng thái đơn
//   POST /api/sepay                                -> webhook SePay (Authorization: Apikey <SEPAY_WEBHOOK_KEY>)
// Biến: SALES_OPEN, SEPAY_ACC, SEPAY_BANK (vars); SEPAY_WEBHOOK_KEY (secret).
// Giao hàng làm tay: đơn 'paid' là đã nhận tiền, gửi gói vào email của đơn rồi đánh 'delivered'.
import { PRODUCTS } from './products.js';

const CODE_RE = /CWD[A-Z0-9]{6}/;
const ALPHA = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' } });

function newCode() {
  const b = crypto.getRandomValues(new Uint8Array(6));
  return 'CWD' + Array.from(b, x => ALPHA[x % ALPHA.length]).join('');
}

function sameKey(a, b) {
  const enc = new TextEncoder(), x = enc.encode(a), y = enc.encode(b);
  if (x.length !== y.length) return false;
  let d = 0;
  for (let i = 0; i < x.length; i++) d |= x[i] ^ y[i];
  return d === 0;
}

async function createOrder(req, env) {
  if (env.SALES_OPEN !== '1') return json({ error: 'chưa mở' }, 403);
  let body;
  try { body = await req.json(); } catch { return json({ error: 'body không hợp lệ' }, 400); }
  const p = PRODUCTS[body.pack];
  if (!p || !p.price) return json({ error: 'chưa mở' }, 403);
  const email = String(body.email || '').trim().slice(0, 200);
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return json({ error: 'email không hợp lệ' }, 400);
  if (!env.SEPAY_ACC || !env.SEPAY_BANK) return json({ error: 'chưa cấu hình tài khoản nhận' }, 503);
  let code;
  for (let i = 0; i < 5; i++) {
    code = newCode();
    const r = await env.DB.prepare('INSERT OR IGNORE INTO orders (code, pack, amount, email) VALUES (?, ?, ?, ?)')
      .bind(code, body.pack, p.price, email).run();
    if (r.meta.changes) break;
    code = null;
  }
  if (!code) return json({ error: 'thử lại' }, 500);
  const qr = `https://qr.sepay.vn/img?acc=${encodeURIComponent(env.SEPAY_ACC)}&bank=${encodeURIComponent(env.SEPAY_BANK)}&amount=${p.price}&des=${code}`;
  return json({ code, amount: p.price, qr, acc: env.SEPAY_ACC, bank: env.SEPAY_BANK });
}

async function getOrder(code, env) {
  const o = await env.DB.prepare('SELECT code, pack, amount, status FROM orders WHERE code = ?').bind(code).first();
  return o ? json(o) : json({ error: 'không có đơn' }, 404);
}

async function sepay(req, env, ctx) {
  const auth = req.headers.get('authorization') || '';
  if (!env.SEPAY_WEBHOOK_KEY || !sameKey(auth, `Apikey ${env.SEPAY_WEBHOOK_KEY}`)) return json({ success: false }, 401);
  let t;
  try { t = await req.json(); } catch { return json({ success: false }, 400); }
  if (t.transferType !== 'in' || !t.id) return json({ success: true });
  const amount = Math.round(Number(t.transferAmount) || 0);
  // Ngân hàng hay bỏ dấu cách/gạch hoặc đổi hoa thường, nên tìm mã trên chuỗi đã làm sạch.
  const flat = `${t.code || ''} ${t.content || ''} ${t.description || ''}`.toUpperCase().replace(/[^A-Z0-9]/g, '');
  const code = (flat.match(CODE_RE) || [])[0] || null;
  const ins = await env.DB.prepare('INSERT OR IGNORE INTO payments (id, code, amount, content, raw) VALUES (?, ?, ?, ?, ?)')
    .bind(t.id, code, amount, String(t.content || ''), JSON.stringify(t).slice(0, 4000)).run();
  if (!ins.meta.changes) return json({ success: true }); // đã xử lý giao dịch này
  if (code) {
    await env.DB.prepare("UPDATE orders SET status = 'paid', paid_at = datetime('now') WHERE code = ? AND status = 'pending' AND amount <= ?")
      .bind(code, amount).run();
  }
  return json({ success: true });
}

export default {
  async fetch(req, env, ctx) {
    const { pathname } = new URL(req.url);
    if (pathname === '/api/sepay' && req.method === 'POST') return sepay(req, env, ctx);
    if (pathname === '/api/order' && req.method === 'POST') return createOrder(req, env);
    const m = pathname.match(/^\/api\/order\/(CWD[A-Z0-9]{6})$/);
    if (m && req.method === 'GET') return getOrder(m[1], env);
    if (pathname.startsWith('/api/')) return json({ error: 'not found' }, 404);
    return env.ASSETS.fetch(req);
  },
};
