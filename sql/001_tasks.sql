-- Phase II / Step 1: durable task queue primitive
-- Safe to re-run.

BEGIN;

CREATE TABLE IF NOT EXISTS tasks (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at      timestamptz NOT NULL DEFAULT now(),
  updated_at      timestamptz NOT NULL DEFAULT now(),

  -- Task identity + payload
  type            text NOT NULL,                 -- e.g. "agent.run", "tool.call", "summarize", etc.
  priority        int  NOT NULL DEFAULT 100,     -- lower = higher priority
  payload         jsonb NOT NULL DEFAULT '{}'::jsonb,

  -- Scheduling / ownership
  status          text NOT NULL DEFAULT 'queued', -- queued|running|succeeded|failed|canceled
  available_at    timestamptz NOT NULL DEFAULT now(),
  locked_by       text NULL,                     -- worker id
  locked_at       timestamptz NULL,
  lock_expires_at timestamptz NULL,

  -- Correlation / traceability
  run_id          uuid NULL,                     -- correlate with your EVENT envelopes
  parent_task_id  uuid NULL REFERENCES tasks(id) ON DELETE SET NULL,

  -- Results
  attempts        int NOT NULL DEFAULT 0,
  max_attempts    int NOT NULL DEFAULT 3,
  last_error      text NULL,
  result          jsonb NULL
);

-- basic constraint for known states (keeps things sane)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'tasks_status_check'
  ) THEN
    ALTER TABLE tasks
      ADD CONSTRAINT tasks_status_check
      CHECK (status IN ('queued','running','succeeded','failed','canceled'));
  END IF;
END$$;

-- indexes for claim loops + admin queries
CREATE INDEX IF NOT EXISTS idx_tasks_claim
  ON tasks (status, available_at, priority, created_at);

CREATE INDEX IF NOT EXISTS idx_tasks_locked
  ON tasks (status, lock_expires_at);

CREATE INDEX IF NOT EXISTS idx_tasks_run_id
  ON tasks (run_id);

CREATE INDEX IF NOT EXISTS idx_tasks_type
  ON tasks (type);

-- updated_at auto-touch trigger
CREATE OR REPLACE FUNCTION touch_updated_at() RETURNS trigger AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_tasks_touch_updated_at ON tasks;
CREATE TRIGGER trg_tasks_touch_updated_at
BEFORE UPDATE ON tasks
FOR EACH ROW EXECUTE FUNCTION touch_updated_at();

COMMIT;
