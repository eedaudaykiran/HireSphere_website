import json
import psycopg2
 
conn = psycopg2.connect(
    dbname='jobportal_db',
    user='postgres',
    password='Uday123',
    host='localhost',
    port='5432'
)
cursor = conn.cursor()
 
with open('sqlite_backup.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
 
jobs = data['core_job']
print('Total jobs in backup:', len(jobs))
print('Columns:', list(jobs[0].keys()))
print()
 
for i, job in enumerate(jobs):
    job = dict(job)
 
    # FIX 1: Added 'is_featured' — was missing before
    for col in ['is_active', 'is_sponsored', 'is_featured', 'salary_disclosed']:
        if col in job and job[col] is not None:
            job[col] = bool(job[col])
 
    cols = list(job.keys())
    vals = [job[c] for c in cols]
    placeholders = ','.join(['%s'] * len(cols))
    sql = f"INSERT INTO core_job ({','.join(cols)}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
 
    try:
        cursor.execute(sql, vals)
        conn.commit()
        print(f"Job {i+1} OK: {job.get('title', '?')}")
    except Exception as e:
        conn.rollback()
        print(f"Job {i+1} FAILED: {job.get('title', '?')}")
        print(f"  ERROR: {e}")
 
# FIX 2: Reset sequence after inserting all jobs
# Without this, the next job created in Django would get id=1 and crash
print("\nFixing core_job sequence...")
try:
    cursor.execute("""
        SELECT setval(
            pg_get_serial_sequence('core_job', 'id'),
            COALESCE((SELECT MAX(id) FROM core_job), 1)
        )
    """)
    conn.commit()
    print("✅ core_job sequence fixed")
except Exception as e:
    conn.rollback()
    print(f"⚠️  Sequence fix failed — {e}")
 
cursor.close()
conn.close()
print("\nDone.")