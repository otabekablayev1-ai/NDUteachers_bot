import psycopg2

conn = psycopg2.connect(
    dbname="YOUR_DB",
    user="YOUR_USER",
    password="YOUR_PASSWORD",
    host="localhost"
)

def search_orders(first_name, last_name):
    query = f"{first_name} {last_name}"

    cur = conn.cursor()

    cur.execute("""
        SELECT file_name, drive_link
        FROM orders
        WHERE content ILIKE %s
        LIMIT 10
    """, (f"%{query}%",))

    rows = cur.fetchall()

    return [
        {"name": r[0], "link": r[1]}
        for r in rows
    ]