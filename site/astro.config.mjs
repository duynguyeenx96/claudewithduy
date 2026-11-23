import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';

// SITE_URL / BASE_PATH đặt trong CI. Cloudflare Pages hoặc domain riêng: để BASE_PATH trống.
// GitHub Pages dạng user.github.io/claudewithduy: BASE_PATH=/claudewithduy
export default defineConfig({
  site: process.env.SITE_URL || 'https://claudewithduy.io.vn',
  base: process.env.BASE_PATH || '/',
  trailingSlash: 'ignore',
  integrations: [
    // Sinh sitemap-index.xml + sitemap-0.xml cho Google/Bing (bỏ trang 404).
    sitemap({ filter: (page) => !/\/(404|mua)\/?$/.test(page) }),
  ],
});
