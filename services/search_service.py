import os
import psycopg2


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL topilmadi")

    return psycopg2.connect(database_url)


def search_orders(first_name, last_name):
    query = f"{first_name} {last_name}"

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT file_name, drive_link
            FROM orders
            WHERE content ILIKE %s
            LIMIT 10
            """,
            (f"%{query}%",)
        )
        rows = cur.fetchall()

        return [{"name": r[0], "link": r[1]} for r in rows]
    finally:
        conn.close()