/// <reference types="vite/client" />

/**
 * NEXORA — Vite Environment Variables
 *
 * Only variables that the browser-side React app legitimately needs are
 * declared here. All AI secrets (Gemini, Whisper) and database
 * credentials (PostgreSQL pgvector) live exclusively in the FastAPI backend
 * environment and must NEVER appear here.
 */
interface ImportMetaEnv {
  /** Base URL for the FastAPI REST backend. e.g. http://localhost:8000/api/v1 */
  readonly VITE_API_BASE_URL: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}