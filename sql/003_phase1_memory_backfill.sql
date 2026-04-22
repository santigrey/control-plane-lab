-- 003_phase1_memory_backfill.sql
-- Phase 1 of unified_alexandra_spec_v1 — metadata backfill for pre-v1 rows
-- Ratified commit: 7664a20
-- Spec ref: docs/unified_alexandra_spec_v1.md §1.4
--
-- Separate from 002 so a schema rollback doesn't require re-applying backfill,
-- and a backfill fix doesn't perturb the schema migration.
-- Idempotent: all UPDATEs guard on column IS NULL.

-- UP
BEGIN;

-- posture_origin: chat endpoints → alexandra; private/intimate endpoints → companion;
-- non-chat rows (tools, workers, venice ingests) stay NULL — they weren't produced by a posture.
UPDATE memory SET posture_origin = 'companion'
  WHERE posture_origin IS NULL
    AND (source = 'intimate' OR source LIKE 'chat_private%');

UPDATE memory SET posture_origin = 'alexandra'
  WHERE posture_origin IS NULL
    AND source IN ('chat_user', 'chat_assistant');

-- content_type: venice_ingest → venice; intimate sources → intimate;
-- chat_auto_save → mixed (tool emerged from auto-save over venice-tainted retrieval);
-- everything else → unclassified.
UPDATE memory SET content_type = 'venice'
  WHERE content_type IS NULL
    AND tool = 'venice_ingest';

UPDATE memory SET content_type = 'intimate'
  WHERE content_type IS NULL
    AND (source = 'intimate' OR source LIKE 'chat_private%');

UPDATE memory SET content_type = 'mixed'
  WHERE content_type IS NULL
    AND tool = 'chat_auto_save';

UPDATE memory SET content_type = 'unclassified'
  WHERE content_type IS NULL;

-- importance: 3 (neutral) per spec §1.4.
UPDATE memory SET importance = 3
  WHERE importance IS NULL;

-- provenance: {backfill:true, from_row_created:<created_at>} per spec §1.4.
UPDATE memory SET provenance = jsonb_build_object(
    'backfill', true,
    'from_row_created', created_at
  )
  WHERE provenance IS NULL;

COMMIT;

-- DOWN (commented; reverts all four columns to NULL across the table)
-- BEGIN;
-- UPDATE memory SET
--   posture_origin = NULL,
--   content_type   = NULL,
--   importance     = NULL,
--   provenance     = NULL;
-- COMMIT;
