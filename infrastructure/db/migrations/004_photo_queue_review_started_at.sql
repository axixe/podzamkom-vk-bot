ALTER TABLE photo_queue ADD COLUMN review_started_at TEXT;

CREATE INDEX IF NOT EXISTS idx_photo_queue_pending_id ON photo_queue(status, id);
