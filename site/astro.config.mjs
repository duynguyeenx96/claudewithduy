import { defineConfig } from 'astro/config';

// SITE_URL / BASE_PATH đặt trong CI. Cloudflare Pages hoặc domain riêng: để BASE_PATH trống.
// GitHub Pages dạng user.github.io/claudewithduy: BASE_PATH=/claudewithduy
export default defineConfig({
  site: process.env.SITE_URL || 'https://claudewithduy.io.vn',
  base: process.env.BASE_PATH || '/',
  trailingSlash: 'ignore',
});
