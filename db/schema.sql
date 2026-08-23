-- Cloudflare D1. Applied remotely (and kept here as the source of truth).
-- Database: theaicommit (fa0d5d4b-8907-420f-956f-8fbbd8a854f2)

CREATE TABLE IF NOT EXISTS subscribers (
  email TEXT PRIMARY KEY,
  status TEXT NOT NULL DEFAULT 'pending',
  confirm_token TEXT NOT NULL UNIQUE,
  unsub_token TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL,
  confirmed_at TEXT,
  unsubscribed_at TEXT
);

CREATE TABLE IF NOT EXISTS issues (
  session_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  hook TEXT,
  url TEXT NOT NULL,
  sent_at TEXT NOT NULL,
  sent_count INTEGER NOT NULL DEFAULT 0
);
