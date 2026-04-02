#!/usr/bin/env python3
import sys, os, json, psycopg2

def get_conn():
    return psycopg2.connect(host='127.0.0.1', port=5432, dbname='controlplane',
        user='admin', password=os.getenv('CONTROLPLANE_DB_PASS', 'adminpass'))

def cmd_list():
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id,title,payload FROM agent_tasks WHERE status='approved' AND assigned_to='cc' ORDER BY created_at ASC")
    for r in cur.fetchall(): print(json.dumps({'id':str(r[0]),'title':r[1],'payload':r[2]}))
    cur.close(); conn.close()

def cmd_get(tid):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id,title,payload FROM agent_tasks WHERE id=%s::uuid",(tid,))
    r = cur.fetchone()
    if r: print(json.dumps({'id':str(r[0]),'title':r[1],'payload':r[2]},indent=2))
    else: print(f"Task {tid} not found",file=sys.stderr); sys.exit(1)
    cur.close(); conn.close()

def cmd_complete(tid, result):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE agent_tasks SET status='completed', result=%s, updated_at=NOW() WHERE id=%s::uuid",
        (json.dumps({'output':result}), tid))
    conn.commit(); print(f"Task {tid} marked completed"); cur.close(); conn.close()

def cmd_fail(tid, reason):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("UPDATE agent_tasks SET status='failed', result=%s, updated_at=NOW() WHERE id=%s::uuid",
        (json.dumps({'error':reason}), tid))
    conn.commit(); print(f"Task {tid} marked failed"); cur.close(); conn.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: task_runner.py {list|get|complete|fail} [args...]", file=sys.stderr); sys.exit(1)
    cmd = sys.argv[1]
    if cmd == 'list': cmd_list()
    elif cmd == 'get' and len(sys.argv) == 3: cmd_get(sys.argv[2])
    elif cmd == 'complete' and len(sys.argv) >= 4: cmd_complete(sys.argv[2], ' '.join(sys.argv[3:]))
    elif cmd == 'fail' and len(sys.argv) >= 4: cmd_fail(sys.argv[2], ' '.join(sys.argv[3:]))
    else: print(f"Unknown command or wrong args: {cmd}", file=sys.stderr); sys.exit(1)

if __name__ == '__main__': main()
