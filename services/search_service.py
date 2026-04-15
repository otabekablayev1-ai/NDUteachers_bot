import os
import psycopg2


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL topilmadi")
    return psycopg2.connect(database_url)


def search_orders(first_name, last_name):
    conn = get_connection()
    try:
        cur = conn.cursor()

        search_text = f"{first_name} {last_name}".lower()

        cur.execute(
            """
            SELECT file_id, link
            FROM order_links
            WHERE students_search ILIKE %s
            LIMIT 10
            """,
            (f"%{search_text}%",)
        )

        rows = cur.fetchall()

        return [{"name": r[0], "link": r[1]} for r in rows]

    finally:
        conn.close()