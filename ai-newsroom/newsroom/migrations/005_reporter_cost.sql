ALTER TABLE news ADD COLUMN reporter TEXT DEFAULT '';

CREATE TABLE IF NOT EXISTS cost_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT,                -- image / text
  provider TEXT,            -- aiauto / gemini / ollama
  amount REAL DEFAULT 0,    -- અંદાજિત ₹
  detail TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
