-- ⚡ ન્યુઝ બનતાં જ WhatsApp પર મોકલ્યાનો સમય + રોજનો આંકડો
ALTER TABLE news ADD COLUMN wa_sent_at DATETIME;
ALTER TABLE daily_stats ADD COLUMN wa_instant INTEGER DEFAULT 0;
