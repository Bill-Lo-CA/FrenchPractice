// src/routes/api/question/+server.ts
import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';
import fs from 'node:fs/promises';
import path from 'node:path';

const AUDIO_DIR = path.resolve(process.cwd(), 'static', 'audio');
const ALLOWED_EXT = new Set(['.mp3', '.wav', '.ogg']);

let cachedFiles: string[] | null = null;

async function listAudioFiles(): Promise<string[]> {
  if (cachedFiles) return cachedFiles;

  const entries = await fs.readdir(AUDIO_DIR, { withFileTypes: true });
  const files = entries
    .filter((e) => e.isFile())
    .map((e) => e.name)
    .filter((name) => ALLOWED_EXT.has(path.extname(name).toLowerCase()));

  cachedFiles = files;
  return files;
}

function parseExpectedFromFilename(filename: string): number | null {
  // 取檔名（不含副檔名），抓出數字
  const base = path.parse(filename).name; // e.g. "07" / "42" / "num_12"
  const m = base.match(/\d+/);
  if (!m) return null;
  const n = Number.parseInt(m[0], 10);
  if (Number.isNaN(n)) return null;
  return n;
}

export const GET: RequestHandler = async () => {
  const files = await listAudioFiles();

  if (!files.length) {
    return json(
      { error: `No audio files found in ${AUDIO_DIR}. Put mp3/wav/ogg files there.` },
      { status: 500 }
    );
  }

  const filename = files[Math.floor(Math.random() * files.length)];
  const expected = parseExpectedFromFilename(filename);

  return json({
    id: filename,
    url: `/audio/${encodeURIComponent(filename)}`,
    expected // 作弊先跳過，所以直接回傳正解給前端算分
  });
};
