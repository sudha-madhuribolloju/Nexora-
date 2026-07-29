/**
 * NEXORA — Vite Dev Server + FastAPI Proxy
 *
 * This file is a THIN wrapper around the Vite development server.
 * It does NOT contain any AI logic, database access, or SDK usage.
 *
 * All AI orchestration (Gemini, Whisper) and all vector/relational data
 * persistence (PostgreSQL + pgvector) live exclusively in the FastAPI backend.
 *
 * In development, this server:
 *   1. Runs the Vite HMR middleware for React
 *   2. Optionally proxies /api/* requests to FastAPI at FASTAPI_URL
 *      (avoids CORS issues during local development)
 *
 * In production, this server serves the pre-built static files from /dist.
 *
 * Port selection:
 *   - Preferred Express port : PORT env var (default 3000)
 *   - Preferred HMR WS port  : HMR_PORT env var (default 24678)
 *   Both fall back to the next available port automatically so that
 *   re-runs after a crash / zombie process never produce EADDRINUSE.
 */

import express from "express";
import net from "net";
import path from "path";
import { createServer as createViteServer } from "vite";
import { createProxyMiddleware } from "http-proxy-middleware";
import dotenv from "dotenv";

dotenv.config();

// ── Port utilities ────────────────────────────────────────────────────────────

/**
 * Returns `true` if the given TCP port is currently in use on the local machine.
 * Uses a raw `net.Server` so no extra npm dependency is required.
 */
function isPortInUse(port: number): Promise<boolean> {
  return new Promise((resolve) => {
    const server = net.createServer();

    server.once("error", (err: NodeJS.ErrnoException) => {
      if (err.code === "EADDRINUSE") {
        resolve(true); // port is busy
      } else {
        resolve(false);
      }
    });

    server.once("listening", () => {
      server.close(() => resolve(false)); // port is free
    });

    server.listen(port, "0.0.0.0");
  });
}

/**
 * Starting from `preferredPort`, returns the first TCP port that is NOT in use.
 * Scans sequentially (preferred → preferred+1 → preferred+2 …).
 */
async function findFreePort(preferredPort: number): Promise<number> {
  let port = preferredPort;
  while (await isPortInUse(port)) {
    console.warn(`⚠️  Port ${port} is already in use — trying ${port + 1}…`);
    port++;
  }
  return port;
}

// ── Configuration ─────────────────────────────────────────────────────────────

const app = express();

// Preferred ports — can be overridden via environment variables
const PREFERRED_PORT = parseInt(process.env.PORT ?? "3000", 10);
const PREFERRED_HMR_PORT = parseInt(process.env.HMR_PORT ?? "24678", 10);

// The FastAPI backend URL — all API calls are proxied here in dev
const FASTAPI_URL = process.env.FASTAPI_URL || "http://localhost:8000";

app.use(express.json());

// ── Health check ──────────────────────────────────────────────────────────────

app.get("/health", (_req, res) => {
  res.json({
    status: "healthy",
    role: "vite-dev-proxy",
    backend: FASTAPI_URL,
    timestamp: new Date().toISOString(),
  });
});

// ── FastAPI Proxy ─────────────────────────────────────────────────────────────
// In development, requests to /api/* are forwarded to FastAPI.
// This eliminates browser CORS issues without touching the React app.
// The React app always targets VITE_API_BASE_URL (http://localhost:8000/api/v1),
// so this proxy is only active when the dev server itself is the entry point.

const apiProxy = createProxyMiddleware({
  target: FASTAPI_URL,
  changeOrigin: true,
  on: {
    error: (err, _req, res: any) => {
      console.error("[Proxy] FastAPI unreachable:", err.message);
      res.status(502).json({
        status: "error",
        message: `FastAPI backend is not reachable at ${FASTAPI_URL}. Start it with: uvicorn app.main:app --reload`,
      });
    },
  },
});

app.use("/api", apiProxy);

// ── Vite Dev Server / Static Serve ────────────────────────────────────────────

async function startServer() {
  // ── Resolve free ports BEFORE binding anything ────────────────────────────
  const port = await findFreePort(PREFERRED_PORT);
  const hmrPort = await findFreePort(PREFERRED_HMR_PORT);

  if (process.env.NODE_ENV !== "production") {
    // middlewareMode: true  → Vite does NOT open its own HTTP listener.
    // We still give it an explicit, free HMR port so the WebSocket server
    // never collides with a stale socket from a previous run.
    const vite = await createViteServer({
      server: {
        middlewareMode: true,
        hmr: {
          port: hmrPort,
          // Expose the HMR socket on all interfaces so the browser can reach it
          // even when the dev machine's loopback name differs from "localhost".
          host: "localhost",
        },
      },
      appType: "spa",
    });

    app.use(vite.middlewares);
    console.log("✅ Vite HMR middleware mounted (Development mode).");
    console.log(`🔌 Vite HMR WebSocket listening on ws://localhost:${hmrPort}`);
    console.log(`🔗 FastAPI proxy active → ${FASTAPI_URL}`);
  } else {
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (_req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
    console.log("✅ Serving production static build from /dist.");
  }

  app.listen(port, "0.0.0.0", () => {
    console.log(`\n🚀 NEXORA Dev Server running on http://localhost:${port}`);
    if (port !== PREFERRED_PORT) {
      console.log(
        `   ℹ️  Preferred port ${PREFERRED_PORT} was busy; using ${port} instead.`
      );
    }
    console.log(`   All AI/DB operations handled by FastAPI at ${FASTAPI_URL}`);
  });
}

startServer();
