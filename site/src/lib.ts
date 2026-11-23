import data from './data/modules.json';

export type Mod = (typeof data.modules)[number] & {
  skill?: { req: string[]; cmd: string; plugin?: string; note?: string; only?: string };
  tool?: { line: string; req: string[]; zip?: string };
  credits?: Credit[];
  effects?: { fx: string; desc: string; extra?: boolean }[];
};
export type Credit = { name: string; url: string; by: string; license: string; use: string };

export const site = data.site;
export const modules = data.modules as Mod[];
export const flow = data.flow;
export const topics = data.topics;
export const templates = data.templates;
export const fxPro = (data as any).fxPro as { id: string; name: string; count: string; desc: string }[];
export const fxFree = (data.modules as Mod[]).filter(m => (m as any).group === 'fx');
export const requirements = data.requirements;

/** Đường dẫn nội bộ có tính base (GitHub Pages dạng /claudewithduy/). */
export function u(path: string) {
  const base = import.meta.env.BASE_URL.replace(/\/$/, '');
  return `${base}/${path.replace(/^\//, '')}`;
}

export const repoUrl = `https://github.com/${site.github}`;
export const marketplaceAdd = `/plugin marketplace add ${site.github}`;
export const pluginInstall = (p: string) => `/plugin install ${p}@${site.marketplace}`;
export const toolZip = (z: string) => `${repoUrl}/releases/latest/download/${z}.zip`;
export const sourceUrl = (m: Mod) =>
  m.skill?.plugin ? `${repoUrl}/tree/main/plugins/${m.skill.plugin}` : m.tool?.zip ? `${repoUrl}/tree/main/tools/${m.tool.zip}` : repoUrl;
export const pad = (n: number) => String(n).padStart(2, '0');
export const kinds = (m: Mod) => [m.skill && 'skill', m.tool && 'tool'].filter(Boolean).join(' ');

/** Mạng xã hội đã điền link, theo thứ tự trong modules.json. */
export const social = Object.entries(site.social).filter(([, v]) => v) as [string, string][];
export const socialName: Record<string, string> = { github: 'GitHub', facebook: 'Facebook', tiktok: 'TikTok', youtube: 'YouTube' };
export const socialIcons: Record<string, string> = {
  github: 'M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12',
  tiktok: 'M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z',
  facebook: 'M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z',
  youtube: 'M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z',
};

/** Ảnh trong public/ có tồn tại không (kiểm lúc build) — chưa bỏ ảnh QR thì ẩn khối tương ứng. */
import { existsSync } from 'node:fs';
import { join } from 'node:path';
export const hasPublic = (p: string) => !!p && existsSync(join(process.cwd(), 'public', p));
export const zalo = (site as any).zalo as { link: string; qr: string };
export const donate = (site as any).donate as { qr: string; bank: string; account: string; name: string };
