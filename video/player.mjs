#!/usr/bin/env node
/**
 * dkapps inline terminal video player
 *
 * Pipes the MP4 through the bundled Remotion ffmpeg (image2pipe/png),
 * decodes each PNG frame with pngjs, and renders it as ANSI true-color
 * half-block art (▀) so the video plays inline in any 24-bit color terminal.
 *
 * Usage:
 *   node player.mjs [path/to/video.mp4]
 *   npm run play
 */

import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { PNG } from "pngjs";

// ── Paths ──────────────────────────────────────────────────────────
const __dir = path.dirname(fileURLToPath(import.meta.url));
const FFMPEG_BIN = path.join(
  __dir,
  "node_modules/@remotion/compositor-linux-x64-gnu/ffmpeg/remotion/bin/ffmpeg"
);
const FFMPEG_LIB = path.join(
  __dir,
  "node_modules/@remotion/compositor-linux-x64-gnu/ffmpeg/remotion/lib"
);
const DEFAULT_VIDEO = path.join(__dir, "out/dkapps-intro.mp4");

// ── Args ───────────────────────────────────────────────────────────
const videoPath = process.argv[2] ?? DEFAULT_VIDEO;

if (!existsSync(videoPath)) {
  console.error(`Video not found: ${videoPath}`);
  console.error("Run 'npm run build' first to render the video.");
  process.exit(1);
}
if (!existsSync(FFMPEG_BIN)) {
  console.error("Bundled ffmpeg not found. Run 'npm install' first.");
  process.exit(1);
}

// ── Terminal dimensions ───────────────────────────────────────────
const COLS = process.stdout.columns || 80;
const ROWS = (process.stdout.rows || 24) - 1; // last row = status bar
const W    = COLS;
const H    = ROWS * 2; // ▀ = top pixel (fg), lower half = bottom pixel (bg)

// ── ANSI helpers ──────────────────────────────────────────────────
const HIDE_CURSOR  = "\x1b[?25l";
const SHOW_CURSOR  = "\x1b[?25h";
const RESET        = "\x1b[0m";
const CLEAR        = "\x1b[2J";
const HOME         = "\x1b[H";

function fgBg(tr, tg, tb, br, bg, bb) {
  return `\x1b[38;2;${tr};${tg};${tb}m\x1b[48;2;${br};${bg};${bb}m\u2580${RESET}`;
}

// ── Render one decoded PNG frame to terminal ──────────────────────
function renderFrame(png) {
  // png.data is RGBA, row-major
  const lines = [];
  for (let row = 0; row < ROWS; row++) {
    let line = `\x1b[${row + 1};1H`;
    for (let col = 0; col < W; col++) {
      const topI = ((row * 2)     * png.width + col) * 4;
      const botI = ((row * 2 + 1) * png.width + col) * 4;
      line += fgBg(
        png.data[topI], png.data[topI + 1], png.data[topI + 2],
        png.data[botI], png.data[botI + 1], png.data[botI + 2],
      );
    }
    lines.push(line);
  }
  return lines.join("");
}

// ── Status bar ────────────────────────────────────────────────────
let frameCount = 0;
let startTime  = Date.now();

function statusBar(frame, total) {
  const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
  const fps     = (frameCount / Math.max(0.001, (Date.now() - startTime) / 1000)).toFixed(1);
  const pct     = total ? `${Math.round((frame / total) * 100)}%` : "?%";
  const barW    = Math.max(0, COLS - 28);
  const filled  = total ? Math.round((frame / total) * barW) : 0;
  const bar     = "\u2588".repeat(filled) + "\u2591".repeat(barW - filled);
  const msg     = ` ${bar} ${pct}  ${elapsed}s  ${fps} fps `;
  return `\x1b[${ROWS + 1};1H\x1b[7m${msg.padEnd(COLS).slice(0, COLS)}${RESET}`;
}

// ── Split a raw byte stream on PNG signatures ─────────────────────
const PNG_SIG = Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);

function* splitPNGs(buf) {
  let start = 0;
  let next  = buf.indexOf(PNG_SIG, 1);
  while (next !== -1) {
    yield buf.subarray(start, next);
    start = next;
    next  = buf.indexOf(PNG_SIG, start + 1);
  }
  return buf.subarray(start); // remainder (incomplete frame)
}

function parsePNG(buf) {
  return new Promise((resolve, reject) => {
    const png = new PNG();
    png.parse(buf, (err, data) => {
      if (err) reject(err);
      else resolve(data);
    });
  });
}

// ── Get total frame count via ffprobe-style stderr parse ──────────
async function getTotalFrames() {
  return new Promise((resolve) => {
    const probe = spawn(
      FFMPEG_BIN,
      ["-i", videoPath, "-map", "0:v:0", "-c", "copy", "-f", "null", "-"],
      { env: { ...process.env, LD_LIBRARY_PATH: FFMPEG_LIB }, stdio: "pipe" }
    );
    let stderr = "";
    probe.stderr.on("data", (d) => (stderr += d.toString()));
    probe.on("close", () => {
      const m = stderr.match(/frame=\s*(\d+)/g);
      if (m) {
        const last = m[m.length - 1].match(/\d+/);
        resolve(last ? parseInt(last[0], 10) : 600);
      } else {
        resolve(600); // fallback
      }
    });
  });
}

// ── Main ──────────────────────────────────────────────────────────
async function play() {
  const totalFrames = await getTotalFrames();

  process.stdout.write(HIDE_CURSOR + CLEAR + HOME);
  startTime = Date.now();

  const ffmpeg = spawn(
    FFMPEG_BIN,
    [
      "-i",    videoPath,
      "-vf",   `scale=${W}:${H}`,
      "-vcodec", "png",
      "-f",    "image2pipe",
      "-",
    ],
    {
      env: { ...process.env, LD_LIBRARY_PATH: FFMPEG_LIB },
      stdio: ["ignore", "pipe", "ignore"],
    }
  );

  let accumulated = Buffer.alloc(0);
  let frame       = 0;

  // Queue so we don't overlap renders
  const queue     = [];
  let rendering   = false;

  async function drainQueue() {
    if (rendering) return;
    rendering = true;
    while (queue.length) {
      const pngBuf = queue.shift();
      try {
        const decoded = await parsePNG(pngBuf);
        frame++;
        frameCount++;
        process.stdout.write(renderFrame(decoded) + statusBar(frame, totalFrames));
      } catch { /* skip malformed frame */ }
    }
    rendering = false;
  }

  ffmpeg.stdout.on("data", (chunk) => {
    accumulated = Buffer.concat([accumulated, chunk]);

    // Extract complete PNG frames
    let sigIdx = accumulated.indexOf(PNG_SIG, 1);
    while (sigIdx !== -1) {
      queue.push(accumulated.subarray(0, sigIdx));
      accumulated = accumulated.subarray(sigIdx);
      sigIdx = accumulated.indexOf(PNG_SIG, 1);
    }

    drainQueue();
  });

  ffmpeg.on("close", async () => {
    // Flush last frame
    if (accumulated.length > PNG_SIG.length) {
      queue.push(accumulated);
    }
    await drainQueue();
    process.stdout.write(`\x1b[${ROWS + 1};1H${RESET}${SHOW_CURSOR}\n`);
    process.stdout.write(`Played ${frame}/${totalFrames} frames in ${((Date.now() - startTime) / 1000).toFixed(1)}s\n`);
    process.exit(0);
  });

  process.on("SIGINT", () => {
    ffmpeg.kill();
    process.stdout.write(SHOW_CURSOR + RESET + "\n");
    process.exit(0);
  });
}

play().catch((err) => {
  process.stdout.write(SHOW_CURSOR);
  console.error(err);
  process.exit(1);
});
