CREATE TABLE IF NOT EXISTS news (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id TEXT,
  title TEXT NOT NULL,
  body TEXT DEFAULT '',
  category TEXT DEFAULT 'general',      -- general / breaking / birthday
  source_title TEXT DEFAULT '',
  source_url TEXT DEFAULT '',
  status TEXT DEFAULT 'draft',          -- draft/written/proofread/pending_approval/approved/rejected/published
  score INTEGER DEFAULT 0,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS poster_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  news_id INTEGER,
  template TEXT,
  size TEXT,
  file_path TEXT,
  render_time_ms INTEGER,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS activity_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id TEXT,
  agent TEXT,
  action TEXT,
  news_id INTEGER,
  status TEXT,
  duration_ms INTEGER,
  model_used TEXT,
  message TEXT,
  error_message TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_stats (
  date DATE PRIMARY KEY,
  news_collected INTEGER DEFAULT 0,
  news_selected INTEGER DEFAULT 0,
  news_written INTEGER DEFAULT 0,
  posters_created INTEGER DEFAULT 0,
  approved INTEGER DEFAULT 0,
  rejected INTEGER DEFAULT 0,
  published_fb INTEGER DEFAULT 0,
  published_ig INTEGER DEFAULT 0,
  published_wa INTEGER DEFAULT 0,
  total_runtime_min INTEGER DEFAULT 0,
  errors INTEGER DEFAULT 0
);
