-- એક ઘટના = એક જ પોસ્ટર. ડુપ્લિકેટ ન્યુઝ કયા ન્યુઝનો છે એ નોંધો
ALTER TABLE news ADD COLUMN duplicate_of INTEGER;
ALTER TABLE daily_stats ADD COLUMN duplicates INTEGER DEFAULT 0;
