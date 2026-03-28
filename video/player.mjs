#!/usr/bin/env node
/**
 * dkapps inline terminal video player
 *
 * Strategy (in priority order):
 *   1. chafa  — converts MP4 → animated GIF (once, cached) then plays with
 *               chafa --animate, auto-selecting Kitty/sixel/ANSI protocol
 *   2. ANSI half-block fallback — pure Node.js, zero extra deps
 *
 * Usage:
 *   node player.mjs [path/to/video.mp4]
 *   npm run play
 */

import { spawn, spawnSync } from "node:child_process";
import { existsSync }       from "node:fs";
import { fileURLToPath }    from "node:url";
import path                 from "node:path";

// ── Paths ─────────────────────────────────────────────────────────
const __dir      = path.dirname(fileURLToPath(import.meta.url));
const FFMPEG_BIN = path.join(__dir, "node_modules/@remotion/compositor-linux-x64-gnu/ffmpeg/remotion/bin/ffmpeg");
const FFMPEG_LIB = path.join(__dir, "node_modules/@remotion/compositor-linux-x64-gnu/ffmpeg/remotion/lib");
const DEFAULT_VIDEO = path.join(__dir, "out/dkapps-intro.mp4");

const videoPath = process.argv[2] ?? DEFAULT_VIDEO;

// GIF lives alongside the MP4, named identically but with .gif extension
const gifPath = videoPath.replace(/\.mp4$/i, ".gif");

if (!existsSync(videoPath)) {
  console.error(`Video not found: ${videoPath}`);
  console.error("Run 'npm run build' first.");
  process.exit(1);
}
if (!existsSync(FFMPEG_BIN)) {
  console.error("Bundled ffmpeg not found. Run 'npm install' first.");
  process.exit(1);
}

const FFMPEG_ENV = { ...process.env, LD_LIBRARY_PATH: FFMPEG_LIB };

// ── Terminal size ─────────────────────────────────────────────────
const COLS = process.stdout.columns || 80;
const ROWS = (process.stdout.rows  || 24) - 1;

// ── Detect chafa ─────────────────────────────────────────────────
function hasChafa() {
  return spawnSync("which", ["chafa"], { stdio: "pipe" }).status === 0;
}

// ── Convert MP4 → animated GIF (cached) ──────────────────────────
async function ensureGif() {
  // Skip if already converted and non-empty
  if (existsSync(gifPath)) {
    const { statSync } = await import("node:fs");
    if (statSync(gifPath).size > 0) return;
  }

  console.log("Converting to animated GIF for chafa (one-time)…");

  // Scale to a reasonable width for the terminal; 15 fps keeps GIF small
  const gifWidth = Math.min(COLS * 8, 480) & ~1; // even number, ~60 chars wide

  await new Promise((resolve, reject) => {
    const ff = spawn(
      FFMPEG_BIN,
      [
        "-i",    videoPath,
        "-vf",   `scale=${gifWidth}:-1`,
        "-r",    "15",         // 15 fps output
        "-loop", "0",          // loop forever
        gifPath,
      ],
      { env: FFMPEG_ENV, stdio: ["ignore", "ignore", "pipe"] }
    );

    let stderr = "";
    ff.stderr.on("data", (d) => { stderr += d; process.stdout.write("."); });
    ff.on("close", (code) => {
      process.stdout.write("\n");
      if (code === 0) resolve();
      else reject(new Error(`ffmpeg exited ${code}\n${stderr.slice(-300)}`));
    });
  });
}

// ── chafa player ─────────────────────────────────────────────────
async function playWithChafa() {
  await ensureGif();

  console.log(`Playing via chafa (${COLS}×${ROWS}) — Ctrl+C to stop\n`);

  const chafa = spawn(
    "chafa",
    [
      `--size=${COLS}x${ROWS}`,
      "--animate=on",
      "--stretch",
      gifPath,
    ],
    { stdio: "inherit" }
  );

  chafa.on("error", (e) => { console.error("chafa error:", e.message); process.exit(1); });
  chafa.on("close", (code) => process.exit(code ?? 0));

  process.on("SIGINT", () => {
    chafa.kill();
    process.stdout.write("\x1b[?25h\n");
    process.exit(0);
  });
}

// ── ANSI half-block fallback ──────────────────────────────────────
async function playAnsiBlocks() {
  const { PNG } = await import("pngjs");

  const W = COLS;
  const H = ROWS * 2;

  function fgBg(tr, tg, tb, br, bg, bb) {
    return `\x1b[38;2;${tr};${tg};${tb}m\x1b[48;2;${br};${bg};${bb}m\u2580\x1b[0m`;
  }

  function renderFrame(png) {
    const lines = [];
    for (let row = 0; row < ROWS; row++) {
      let line = `\x1b[${row + 1};1H`;
      for (let col = 0; col < W; col++) {
        const ti = ((row * 2)     * png.width + col) * 4;
        const bi = ((row * 2 + 1) * png.width + col) * 4;
        line += fgBg(
          png.data[ti], png.data[ti+1], png.data[ti+2],
          png.data[bi], png.data[bi+1], png.data[bi+2],
        );
      }
      lines.push(line);
    }
    return lines.join("");
  }

  function parsePNG(buf) {
    return new Promise((res, rej) => {
      const p = new PNG();
      p.parse(buf, (err, data) => err ? rej(err) : res(data));
    });
  }

  const PNG_SIG = Buffer.from([0x89,0x50,0x4e,0x47,0x0d,0x0a,0x1a,0x0a]);

  process.stdout.write("\x1b[?25l\x1b[2J\x1b[H");

  const ffmpeg = spawn(
    FFMPEG_BIN,
    ["-i", videoPath, "-vf", `scale=${W}:${H}`, "-vcodec", "png", "-f", "image2pipe", "-"],
    { env: FFMPEG_ENV, stdio: ["ignore", "pipe", "ignore"] }
  );

  let buf = Buffer.alloc(0);
  let frame = 0;
  const queue = [];
  let rendering = false;

  async function drain() {
    if (rendering) return;
    rendering = true;
    while (queue.length) {
      try {
        const decoded = await parsePNG(queue.shift());
        frame++;
        process.stdout.write(renderFrame(decoded));
      } catch { /* skip malformed frame */ }
    }
    rendering = false;
  }

  ffmpeg.stdout.on("data", (chunk) => {
    buf = Buffer.concat([buf, chunk]);
    let next = buf.indexOf(PNG_SIG, 1);
    while (next !== -1) {
      queue.push(buf.subarray(0, next));
      buf  = buf.subarray(next);
      next = buf.indexOf(PNG_SIG, 1);
    }
    drain();
  });

  ffmpeg.on("close", async () => {
    if (buf.length > PNG_SIG.length) queue.push(buf);
    await drain();
    process.stdout.write(`\x1b[${ROWS+1};1H\x1b[0m\x1b[?25h\n`);
    process.stdout.write(`Played ${frame} frames\n`);
    process.exit(0);
  });

  process.on("SIGINT", () => {
    ffmpeg.kill();
    process.stdout.write("\x1b[?25h\x1b[0m\n");
    process.exit(0);
  });
}

// ── Entry point ───────────────────────────────────────────────────
if (hasChafa()) {
  playWithChafa();
} else {
  console.warn("chafa not found — falling back to ANSI half-block renderer");
  console.warn("Install for better quality: apt install chafa\n");
  playAnsiBlocks();
}
