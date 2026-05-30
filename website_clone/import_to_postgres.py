import json
import psycopg2
from psycopg2.extras import execute_values
 
# ── CHANGE THESE to match your PostgreSQL settings ──
DB_NAME     = 'jobportal_db'
DB_USER     = 'postgres'
DB_PASSWORD = 'Uday@123eeda'
DB_HOST     = 'localhost'
DB_PORT     = '5432'
# ────────────────────────────────────────────────────
 
# SQLite stores booleans as 0/1 integers.
# These are all the boolean columns in your models.
BOOLEAN_COLUMNS = {
    'auth_user':            ['is_superuser', 'is_staff', 'is_active'],
    'core_userprofile':     ['email_verified'],
    'core_job':             ['is_active', 'is_sponsored', 'salary_disclosed'],
    'core_application':     [],
    'core_message':         ['is_read'],
    'core_employersettings':['email_notifications', 'sms_notifications',
                             'application_alerts', 'profile_views'],
    'core_interview':       [],
    'core_savedjob':        [],
    'core_companyprofile':  [],
}
 
# Tables in correct FK order (parents before children)
TABLE_ORDER = [
    'django_content_type',
    'auth_permission',
    'auth_user',            # must come before everything that FK's to user
    'auth_group',
    'auth_group_permissions',
    'auth_user_groups',
    'auth_user_user_permissions',
    'core_userprofile',
    'core_companyprofile',
    'core_employersettings',
    'core_job',             # must come before application, savedjob
    'core_application',
    'core_applyjob',
    'core_savedjob',
    'core_interview',
    'core_message',
    'core_emailverification',
    'django_admin_log',
    'django_session',
]
 
def fix_booleans(table, rows):
    """Convert 0/1 integers to True/False for boolean columns."""
    bool_cols = BOOLEAN_COLUMNS.get(table, [])
    if not bool_cols:
        return rows
    fixed = []
    for row in rows:
        row = dict(row)
        for col in bool_cols:
            if col in row and row[col] is not None:
                row[col] = bool(row[col])
        fixed.append(row)
    return fixed
 
def fix_content_type_ids(rows, ct_id_map):
    """Remap content_type_id values to match what's actually in PostgreSQL."""
    fixed = []
    for row in rows:
        row = dict(row)
        if 'content_type_id' in row and row['content_type_id'] in ct_id_map:
            row['content_type_id'] = ct_id_map[row['content_type_id']]
        fixed.append(row)
    return fixed
 
print("=" * 50)
print("Loading sqlite_backup.json...")
with open('sqlite_backup.json', 'r', encoding='utf-8') as f:
    all_data = json.load(f)
print("✅ Backup loaded\n")
 
print("Connecting to PostgreSQL...")
conn = psycopg2.connect(
    dbname=DB_NAME, user=DB_USER,
    password=DB_PASSWORD, host=DB_HOST, port=DB_PORT
)
conn.autocommit = False
cursor = conn.cursor()
print("✅ Connected\n")
 
# Step 1: Clear all existing data in reverse FK order to avoid conflicts
print("Clearing existing PostgreSQL data...")
clear_order = list(reversed(TABLE_ORDER))
for table in clear_order:
    try:
        cursor.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
        conn.commit()
    except Exception:
        conn.rollback()
print("✅ Cleared\n")
 
# Step 2: Build a content_type ID map
# PostgreSQL may have different IDs for content types than SQLite
sqlite_cts  = {(r['app_label'], r['model']): r['id'] for r in all_data.get('django_content_type', [])}
ct_id_map   = {}  # sqlite_id -> postgres_id (filled after inserting content types)
 
# Step 3: Import each table
print("Importing data...\n")
for table in TABLE_ORDER:
    rows = all_data.get(table, [])
    if not rows:
        print(f"  SKIP  {table} — 0 records")
        continue
 
    # Fix booleans
    rows = fix_booleans(table, rows)
 
    # Fix content_type_id references (for auth_permission, django_admin_log)
    if table in ('auth_permission', 'django_admin_log'):
        rows = fix_content_type_ids(rows, ct_id_map)
 
    columns = list(rows[0].keys())
    values  = [tuple(row.get(col) for col in columns) for row in rows]
 
    try:
        execute_values(
            cursor,
            f"INSERT INTO {table} ({', '.join(columns)}) VALUES %s ON CONFLICT DO NOTHING",
            values
        )
        conn.commit()
        print(f"  ✅  {table}: {len(rows)} records inserted")
 
        # After inserting content types, build the ID map
        if table == 'django_content_type':
            cursor.execute("SELECT id, app_label, model FROM django_content_type")
            pg_cts = cursor.fetchall()
            for pg_id, app_label, model in pg_cts:
                sqlite_id = sqlite_cts.get((app_label, model))
                if sqlite_id:
                    ct_id_map[sqlite_id] = pg_id
 
    except Exception as e:
        conn.rollback()
        print(f"  ❌  {table}: FAILED — {e}")
 
# Step 4: Fix all sequences so new records don't conflict
print("\nFixing sequences...")
sequence_tables = [
    'auth_user', 'auth_permission', 'django_content_type',
    'core_job', 'core_userprofile', 'core_application',
    'core_interview', 'core_message', 'core_savedjob',
    'core_companyprofile', 'core_employersettings',
]
for table in sequence_tables:
    try:
        cursor.execute(f"""
            SELECT setval(
                pg_get_serial_sequence('{table}', 'id'),
                COALESCE((SELECT MAX(id) FROM {table}), 1)
            )
        """)
        conn.commit()
        print(f"  ✅  {table} sequence fixed")
    except Exception as e:
        conn.rollback()
        print(f"  ⚠️   {table} sequence skip — {e}")
 
cursor.close()
conn.close()
 
print("\n" + "=" * 50)
print("🎉 Import complete! Now verify in Django shell:")
print("   python manage.py shell")
print("   >>> from core.models import Job, Application")
print("   >>> from django.contrib.auth.models import User")
print("   >>> print(User.objects.count())        # should be 24")
print("   >>> print(Job.objects.count())         # should be 27")
print("   >>> print(Application.objects.count()) # should be 13")