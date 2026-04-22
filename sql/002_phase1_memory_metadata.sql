-- 002_phase1_memory_metadata.sql
-- Phase 1 of unified_alexandra_spec_v1 — memory metadata columns
-- Ratified commit: 7664a20
-- Spec ref: docs/unified_alexandra_spec_v1.md §1.1
--
-- Adds four nullable metadata columns to memory table.
-- No behavior change. Backfill is a separate migration (003).

-- UP
BEGIN;

ALTER TABLE memory
  ADD COLUMN posture_origin TEXT,
  ADD COLUMN content_type   TEXT,
  ADD COLUMN importance     INT,
  ADD COLUMN provenance     JSONB;

COMMIT;

-- DOWN (commented; apply manually to revert)
-- BEGIN;
-- ALTER TABLE memory
--   DROP COLUMN IF EXISTS provenance,
--   DROP COLUMN IF EXISTS importance,
--   DROP COLUMN IF EXISTS content_type,
--   DROP COLUMN IF EXISTS posture_origin;
-- COMMIT;
