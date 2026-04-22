ALTER TABLE user_drafts ADD COLUMN file_id TEXT;

CREATE INDEX IF NOT EXISTS idx_user_drafts_user_id_created_at ON user_drafts(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_user_drafts_file_id ON user_drafts(file_id);
