#!/usr/bin/env node
/**
 * dkapps video download server
 *
 * Serves the out/ directory over HTTP so you can download the rendered
 * video directly from your browser.
 *
 * Usage:
 *   node serve.mjs
 *   npm run serve
 *
 * Then open the printed URL in your browser and click the MP4 link.
 */

import http from "node:http";
import fs   from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dir  = path.dirname(fileURLToPath(import.meta.url));
const outDir = path.join(__dir, "out");
const PORT   = Number(process.env.PORT) || 3001;

const MIME = {
  ".mp4": "video/mp4",
  ".gif": "image/gif",
  ".mov": "video/quicktime",
  ".webm": "video/webm",
};

function listPage(files) {
  const rows = files.map((f) => {
    const stats = fs.statSync(path.join(outDir, f));
    const kb    = (stats.size / 1024).toFixed(0);
    return `
      <tr>
        <td><a href="/${encodeURIComponent(f)}" download="${f}">⬇ ${f}</a></td>
        <td>${kb} KB</td>
        <td><a href="/${encodeURIComponent(f)}" target="_blank">preview</a></td>
      </tr>`;
  }).join("");

  return `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>dkapps video downloads</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 640px; margin: 60px auto; padding: 0 20px; background: #0a0e1a; color: #f8fafc; }
    h1   { background: linear-gradient(135deg,#6366f1,#22d3ee); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    table{ width: 100%; border-collapse: collapse; margin-top: 24px; }
    td   { padding: 12px 16px; border-bottom: 1px solid #ffffff18; }
    a    { color: #22d3ee; text-decoration: none; font-weight: 600; }
    a:hover { text-decoration: underline; }
  </style>
</head>
<body>
  <h1>dkapps · video downloads</h1>
  <p style="color:#94a3b8">Click a file below — your browser will prompt you to save it.</p>
  <table>${rows}</table>
</body>
</html>`;
}

const server = http.createServer((req, res) => {
  const urlPath = decodeURIComponent(req.url.split("?")[0]);

  // Root → file listing
  if (urlPath === "/") {
    const files = fs.readdirSync(outDir).filter((f) =>
      fs.statSync(path.join(outDir, f)).isFile()
    );
    res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
    return res.end(listPage(files));
  }

  // File download
  const file = path.join(outDir, path.basename(urlPath));
  if (!file.startsWith(outDir) || !fs.existsSync(file)) {
    res.writeHead(404);
    return res.end("Not found");
  }

  const ext  = path.extname(file).toLowerCase();
  const mime = MIME[ext] || "application/octet-stream";
  const stat = fs.statSync(file);

  res.writeHead(200, {
    "Content-Type":        mime,
    "Content-Length":      stat.size,
    "Content-Disposition": `attachment; filename="${path.basename(file)}"`,
  });
  fs.createReadStream(file).pipe(res);
});

server.listen(PORT, "0.0.0.0", () => {
  const url = `http://localhost:${PORT}`;
  console.log(`\n  dkapps video server running`);
  console.log(`\n  Open this URL in your browser:\n`);
  console.log(`    \x1b[36m${url}\x1b[0m\n`);
  console.log(`  Direct download link:\n`);
  console.log(`    \x1b[36m${url}/dkapps-intro.mp4\x1b[0m\n`);
  console.log(`  Press Ctrl+C to stop.\n`);
});

process.on("SIGINT", () => { server.close(); process.exit(0); });
