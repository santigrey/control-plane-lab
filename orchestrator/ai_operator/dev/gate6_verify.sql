\set ON_ERROR_STOP on

-- task totals
SELECT status, count(*)
FROM tasks
GROUP BY status
ORDER BY status;

-- active workers
SELECT worker_id, started_at, last_seen_at, poll_s, lock_s
FROM worker_heartbeats
ORDER BY last_seen_at DESC
LIMIT 10;

-- last events
SELECT created_at, source, tool, left(content,220) AS content220
FROM memory
ORDER BY created_at DESC
LIMIT 30;
