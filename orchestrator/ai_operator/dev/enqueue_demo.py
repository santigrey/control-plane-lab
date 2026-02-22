import json
import psycopg
from ai_operator.memory.db import get_db_url

TASKS = [
    {"type": "tool.call", "payload": {"tool": "ping", "args": {"message": "demo_1"}}, "priority": 10},
    {"type": "tool.call", "payload": {"tool": "sleep", "args": {"seconds": 2}}, "priority": 10},
    {"type": "tool.call", "payload": {"tool": "ping", "args": {"message": "demo_2"}}, "priority": 10},
]

SQL = """
INSERT INTO tasks (type, payload, priority)
VALUES (%(type)s, %(payload)s::jsonb, %(priority)s)
RETURNING id;
"""

def main():
    db_url = get_db_url()
    with psycopg.connect(db_url) as conn:
        with conn.cursor() as cur:
            for t in TASKS:
                cur.execute(SQL, {
                    "type": t["type"],
                    "payload": json.dumps(t["payload"]),
                    "priority": t["priority"],
                })
                tid = cur.fetchone()[0]
                print("ENQUEUED", tid)
        conn.commit()

if __name__ == "__main__":
    main()
