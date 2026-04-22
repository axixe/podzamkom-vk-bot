ALTER TABLE employees ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1;
ALTER TABLE employees ADD COLUMN updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP;

UPDATE employees
SET is_active = 1,
    updated_at = COALESCE(updated_at, created_at);
