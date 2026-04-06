#!/usr/bin/env python3
import subprocess, psycopg2, logging, sys

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
log = logging.getLogger('sync_app_count')

def main():
    try:
        result = subprocess.run(
            ['ssh', '-i', '/home/jes/.ssh/id_ed25519', '-o', 'StrictHostKeyChecking=no', '-o', 'ConnectTimeout=10',
             'jes@192.168.1.13', 'wc -l /Users/jes/AI_Agent_OS/job-search/applications.csv'],
            capture_output=True, text=True, timeout=15
        )
        if result.returncode != 0:
            log.error(f'SSH failed: {result.stderr.strip()}')
            return
        line_count = int(result.stdout.strip().split()[0])
        app_count = max(0, line_count - 1)  # subtract header

        conn = psycopg2.connect(host='127.0.0.1', port=5432, dbname='controlplane', user='admin', password='adminpass')
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO user_profile (category,key,value,source) VALUES ('context','application_count',%s,'sync') "
            "ON CONFLICT (category,key) DO UPDATE SET value=EXCLUDED.value, source=EXCLUDED.source, updated_at=NOW()",
            (str(app_count),)
        )
        conn.commit()
        cur.close()
        conn.close()
        log.info(f'Synced application count: {app_count}')
    except subprocess.TimeoutExpired:
        log.error('SSH to Mac mini timed out')
    except Exception as e:
        log.error(f'Sync failed: {e}')

if __name__ == '__main__':
    main()
