cur = conn.cursor()

print("📋 Ustunlar ro‘yxati:")
cur.execute("PRAGMA table_info(teachers)")
for col in cur.fetchall():
    print(col)

print("\n📊 Bir nechta yozuvlar:")
cur.execute("SELECT fio, faculty, department, role FROM teachers LIMIT 10")
for row in cur.fetchall():
    print(row)

conn.close()
