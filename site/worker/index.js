// Worker của site: /api/* xử lý ở đây, còn lại trả file tĩnh trong dist.
//   POST /api/order          {pack, email}  -> tạo đơn + QR + secret (chỉ khi SALES_OPEN = "1" và gói có giá)
//   GET  /api/order/:code?t=<secret>        -> trạng thái đơn; đã trả thì kèm link tải
//   POST /api/sepay                          -> webhook SePay (Authorization: Apikey <SEPAY_WEBHOOK_KEY>)
//   GET  /api/download/:token                -> tải zip của gói từ R2 (7 ngày, 5 lượt)
// Tiền vào khớp đơn: tạo link tải, gửi biên nhận cho người mua, báo chủ shop. Tiền vào lạ: chỉ báo chủ shop.
// Biến: SALES_OPEN, DOWNLOADS_OPEN ("0" = khoá mọi link tải, không đụng R2), SEPAY_ACC, SEPAY_BANK, SITE_URL, MAIL_FROM (vars);
//       SEPAY_WEBHOOK_KEY, RESEND_API_KEY, NOTIFY_EMAIL (secret). R2: FILES, file <pack>.zip.
import { PRODUCTS } from './products.js';

const CODE_RE = /CWD[A-Z0-9]{6}/;
const ALPHA = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789';
const LINK_DAYS = 7;
// QR ủng hộ trên site (public/qr/bank.png) có sẵn nội dung "Ung ho Duy ly cafe".
const DONATE_RE = /UNGHO|CAFE|COFFEE/;
// Nhóm Zalo, giống site.zalo trong src/data/modules.json; ảnh QR lấy từ /qr/zalo.png của site.
const ZALO_LINK = 'https://zaloapp.com/qr/g/nhc375qne8derj2qluti';

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' } });
const text = (s, status) => new Response(s, { status, headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'no-store' } });

function newCode() {
  const b = crypto.getRandomValues(new Uint8Array(6));
  return 'CWD' + Array.from(b, x => ALPHA[x % ALPHA.length]).join('');
}
const randHex = n => Array.from(crypto.getRandomValues(new Uint8Array(n)), x => x.toString(16).padStart(2, '0')).join('');

function sameKey(a, b) {
  const enc = new TextEncoder(), x = enc.encode(a), y = enc.encode(b);
  if (x.length !== y.length) return false;
  let d = 0;
  for (let i = 0; i < x.length; i++) d |= x[i] ^ y[i];
  return d === 0;
}

const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
const vnd = n => Number(n).toLocaleString('vi-VN') + 'đ';
// D1 lưu giờ UTC dạng 'YYYY-MM-DD HH:MM:SS'; email hiện giờ Việt Nam.
const vnTime = utc => new Date(utc.replace(' ', 'T') + 'Z').toLocaleString('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh', hour12: false });

async function createOrder(req, env) {
  if (env.SALES_OPEN !== '1') return json({ error: 'chưa mở' }, 403);
  let body;
  try { body = await req.json(); } catch { return json({ error: 'body không hợp lệ' }, 400); }
  const p = PRODUCTS[body.pack];
  if (!p || !p.price) return json({ error: 'chưa mở' }, 403);
  const email = String(body.email || '').trim().slice(0, 200);
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) return json({ error: 'email không hợp lệ' }, 400);
  if (!env.SEPAY_ACC || !env.SEPAY_BANK) return json({ error: 'chưa cấu hình tài khoản nhận' }, 503);
  const secret = randHex(16);
  let code;
  for (let i = 0; i < 5; i++) {
    code = newCode();
    const r = await env.DB.prepare('INSERT OR IGNORE INTO orders (code, pack, amount, email, secret) VALUES (?, ?, ?, ?, ?)')
      .bind(code, body.pack, p.price, email, secret).run();
    if (r.meta.changes) break;
    code = null;
  }
  if (!code) return json({ error: 'thử lại' }, 500);
  const qr = `https://qr.sepay.vn/img?acc=${encodeURIComponent(env.SEPAY_ACC)}&bank=${encodeURIComponent(env.SEPAY_BANK)}&amount=${p.price}&des=${code}`;
  return json({ code, secret, amount: p.price, qr, acc: env.SEPAY_ACC, bank: env.SEPAY_BANK });
}

async function getOrder(code, t, env) {
  const o = await env.DB.prepare('SELECT code, pack, amount, status, secret FROM orders WHERE code = ?').bind(code).first();
  if (!o) return json({ error: 'không có đơn' }, 404);
  const out = { code: o.code, pack: o.pack, amount: o.amount, status: o.status };
  if (o.status !== 'pending' && o.secret && t && sameKey(t, o.secret)) {
    const d = await env.DB.prepare("SELECT token FROM downloads WHERE code = ? AND expires_at > datetime('now') AND uses < max_uses ORDER BY expires_at DESC LIMIT 1").bind(code).first();
    if (d) out.download = `${env.SITE_URL}/api/download/${d.token}`;
  }
  return json(out);
}

async function newLink(code, env) {
  const token = randHex(24);
  await env.DB.prepare(`INSERT INTO downloads (token, code, expires_at) VALUES (?, ?, datetime('now', '+${LINK_DAYS} days'))`).bind(token, code).run();
  return `${env.SITE_URL}/api/download/${token}`;
}

async function download(token, env) {
  if (env.DOWNLOADS_OPEN === '0') return text('Tạm dừng tải trong ít phút. Link của bạn vẫn giữ nguyên, thử lại sau nhé.', 503);
  const d = await env.DB.prepare('SELECT d.code, d.uses, d.max_uses, d.expires_at > datetime(\'now\') AS live, o.pack FROM downloads d JOIN orders o ON o.code = d.code WHERE d.token = ?').bind(token).first();
  if (!d) return text('Link không đúng.', 404);
  if (!d.live || d.uses >= d.max_uses) return text('Link đã hết hạn hoặc hết lượt tải. Trả lời email biên nhận để nhận link mới.', 410);
  const obj = env.FILES && await env.FILES.get(`${d.pack}.zip`);
  if (!obj) return text('File đang được cập nhật, thử lại sau ít phút.', 503);
  await env.DB.prepare('UPDATE downloads SET uses = uses + 1 WHERE token = ?').bind(token).run();
  return new Response(obj.body, {
    headers: { 'content-type': 'application/zip', 'content-disposition': `attachment; filename="${d.pack}.zip"`, 'content-length': String(obj.size), 'cache-control': 'no-store' },
  });
}

async function sendMail(env, to, subject, html, plain, replyTo) {
  if (!env.RESEND_API_KEY || !to) return 'không có RESEND_API_KEY hoặc người nhận';
  const r = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { authorization: `Bearer ${env.RESEND_API_KEY}`, 'content-type': 'application/json' },
    body: JSON.stringify({ from: env.MAIL_FROM, to: [to], subject, html, text: plain, ...(replyTo ? { reply_to: replyTo } : {}) }),
  });
  return r.ok ? null : `resend ${r.status}: ${(await r.text()).slice(0, 300)}`;
}

function receipt(o, p, link, t, env) {
  const rows = [
    ['Mã đơn', o.code], ['Gói', p.name], ['Số tiền', vnd(o.amount)],
    ['Thời gian', vnTime(o.paid_at)], ['Mã giao dịch', t.referenceCode || t.id],
  ];
  const html = `<div style="font-family:-apple-system,Segoe UI,Roboto,sans-serif;max-width:520px;margin:0 auto;color:#1a1a1a;line-height:1.55">
<p>Chào bạn,</p>
<p>Mình đã nhận được tiền cho đơn <b>${esc(o.code)}</b>. Cảm ơn bạn đã ủng hộ.</p>
<p style="margin:24px 0"><a href="${esc(link)}" style="background:#c2410c;color:#fff;text-decoration:none;padding:12px 20px;border-radius:6px;display:inline-block">Tải ${esc(p.name)}</a></p>
<p style="font-size:14px;color:#555">Link dùng được ${LINK_DAYS} ngày, tối đa 5 lần tải. Hết hạn thì trả lời email này, mình gửi link mới.</p>
<h3 style="font-size:15px;margin:28px 0 8px">Biên nhận thanh toán</h3>
<table style="border-collapse:collapse;font-size:14px;width:100%">${rows.map(([k, v]) => `<tr><td style="padding:6px 0;color:#666;border-bottom:1px solid #eee">${k}</td><td style="padding:6px 0;text-align:right;border-bottom:1px solid #eee">${esc(v)}</td></tr>`).join('')}</table>
<p style="font-size:14px;margin-top:24px">Cách cài có trong file README trong gói. Kẹt chỗ nào cứ trả lời email này.</p>
<div style="margin:28px 0;padding:16px;border:1px solid #eee;border-radius:8px;text-align:center">
<p style="margin:0 0 4px;font-weight:600">Vào nhóm Zalo</p>
<p style="margin:0 0 12px;font-size:14px;color:#555">Hỏi cách dùng, xem hiệu ứng mới, góp ý cho gói.</p>
<a href="${ZALO_LINK}"><img src="${env.SITE_URL}/qr/zalo.png" width="160" height="160" alt="Mã QR nhóm Zalo" style="display:block;margin:0 auto 12px;border:0"></a>
<a href="${ZALO_LINK}" style="font-size:14px;color:#c2410c">Đang xem trên điện thoại? Bấm vào đây để vào nhóm</a>
</div>
<p>Duy<br><a href="https://claudewithduy.io.vn" style="color:#c2410c">claudewithduy.io.vn</a></p>
<p style="font-size:12px;color:#999;margin-top:28px">Đây là biên nhận thanh toán, không phải hoá đơn điện tử.</p>
</div>`;
  const plain = `Chào bạn,\n\nMình đã nhận được tiền cho đơn ${o.code}. Cảm ơn bạn đã ủng hộ.\n\nTải ${p.name}: ${link}\n(Link dùng được ${LINK_DAYS} ngày, tối đa 5 lần tải. Hết hạn thì trả lời email này.)\n\nBIÊN NHẬN THANH TOÁN\n${rows.map(([k, v]) => `${k}: ${v}`).join('\n')}\n\nVào nhóm Zalo (hỏi cách dùng, xem hiệu ứng mới): ${ZALO_LINK}\n\nDuy\nclaudewithduy.io.vn\n\nĐây là biên nhận thanh toán, không phải hoá đơn điện tử.`;
  return { html, plain };
}

// Chạy sau khi đã trả 200 cho SePay.
async function afterPayment(t, code, paid, env) {
  const amount = Math.round(Number(t.transferAmount) || 0);
  if (paid) {
    const o = await env.DB.prepare('SELECT * FROM orders WHERE code = ?').bind(code).first();
    const p = PRODUCTS[o.pack] || { name: o.pack };
    const link = await newLink(code, env);
    const m = receipt(o, p, link, t, env);
    const err = await sendMail(env, o.email, `Biên nhận ${o.code} · ${p.name}`, m.html, m.plain, env.NOTIFY_EMAIL);
    if (err) await env.DB.prepare('UPDATE orders SET note = ? WHERE code = ?').bind(err, code).run();
    else await env.DB.prepare("UPDATE orders SET status = 'delivered', delivered_at = datetime('now') WHERE code = ?").bind(code).run();
    const s = `Đơn mới ${o.code} · ${p.name} · ${vnd(amount)}`;
    const body = `Khách: ${o.email}\nGói: ${p.name}\nSố tiền: ${vnd(amount)}\nNội dung CK: ${t.content || ''}\nEmail biên nhận: ${err ? 'LỖI, ' + err : 'đã gửi'}`;
    await sendMail(env, env.NOTIFY_EMAIL, s, `<pre style="font:14px/1.5 monospace">${esc(body)}</pre>`, body);
  } else if (!code && DONATE_RE.test(`${t.content || ''} ${t.description || ''}`.toUpperCase().replace(/[^A-Z0-9]/g, ''))) {
    const body = `Số tiền: ${vnd(amount)}\nNội dung CK: ${t.content || ''}\nMã giao dịch: ${t.referenceCode || t.id}`;
    await sendMail(env, env.NOTIFY_EMAIL, `Có người ủng hộ ly cà phê ☕ ${vnd(amount)}`, `<pre style="font:14px/1.5 monospace">${esc(body)}</pre>`, body);
  } else {
    const why = code ? `có mã ${code} nhưng không khớp đơn đang chờ (sai số tiền, đơn đã trả, hoặc không có đơn)` : 'không có mã đơn';
    const body = `Số tiền: ${vnd(amount)}\nNội dung CK: ${t.content || ''}\nMã giao dịch: ${t.referenceCode || t.id}\nLý do: ${why}`;
    await sendMail(env, env.NOTIFY_EMAIL, `Tiền vào cần xem tay · ${vnd(amount)}`, `<pre style="font:14px/1.5 monospace">${esc(body)}</pre>`, body);
  }
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
  let paid = false;
  if (code) {
    const up = await env.DB.prepare("UPDATE orders SET status = 'paid', paid_at = datetime('now') WHERE code = ? AND status = 'pending' AND amount <= ?")
      .bind(code, amount).run();
    paid = up.meta.changes > 0;
  }
  ctx.waitUntil(afterPayment(t, code, paid, env).catch(e => console.error('afterPayment', code, e)));
  return json({ success: true });
}

export default {
  async fetch(req, env, ctx) {
    const url = new URL(req.url), { pathname } = url;
    if (pathname === '/api/sepay' && req.method === 'POST') return sepay(req, env, ctx);
    if (pathname === '/api/order' && req.method === 'POST') return createOrder(req, env);
    let m = pathname.match(/^\/api\/order\/(CWD[A-Z0-9]{6})$/);
    if (m && req.method === 'GET') return getOrder(m[1], url.searchParams.get('t'), env);
    m = pathname.match(/^\/api\/download\/([0-9a-f]{48})$/);
    if (m && req.method === 'GET') return download(m[1], env);
    if (pathname.startsWith('/api/')) return json({ error: 'not found' }, 404);
    return env.ASSETS.fetch(req);
  },
};
