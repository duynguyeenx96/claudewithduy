import data from './data/modules.json';

export type Mod = (typeof data.modules)[number] & {
  skill?: { req: string[]; cmd: string; plugin?: string; note?: string; only?: string };
  tool?: { line: string; req: string[]; zip?: string };
};

export const site = data.site;
export const modules = data.modules as Mod[];
export const flow = data.flow;
export const topics = data.topics;
export const templates = data.templates;

/** Đường dẫn nội bộ có tính base (GitHub Pages dạng /ke-module/). */
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
