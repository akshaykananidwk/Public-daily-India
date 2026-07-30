ALTER TABLE news ADD COLUMN reporter TEXT DEFAULT '';

CREATE TABLE IF NOT EXISTS cost_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  kind TEXT,                -- image / text
  provider TEXT,            -- gemini / openai / pollinations / local / ollama
  amount REAL DEFAULT 0,    -- અંદાજિત ₹
  detail TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
