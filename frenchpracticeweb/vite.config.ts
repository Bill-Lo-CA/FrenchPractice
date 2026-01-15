import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    // 允許 ngrok 免費網域的任意子網域（你每次 ngrok 產生的字串會變，用這個最省事）
    allowedHosts: ['.ngrok-free.dev'],

    // 如果你想更嚴格，只允許當次那一個網址，就用下面這種：
    // allowedHosts: ['unspecifying-unalliterated-wenona.ngrok-free.dev'],
  },

  // 如果你之後用 bun run preview，也可以順手加（預設會沿用 server.allowedHosts）
  // preview: {
  //   allowedHosts: ['.ngrok-free.dev'],
  // },
});
