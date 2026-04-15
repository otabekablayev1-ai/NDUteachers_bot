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
            SELECT id, link
            FROM order_links
            WHERE students_search ILIKE %s
               OR students_raw ILIKE %s
               OR title ILIKE %s
            LIMIT 10
            """,
            (f"%{query}%", f"%{query}%", f"%{query}%")
        )
        rows = cur.fetchall()

        return [
            {
                "file_id": r[0],
                "link": r[1]
            }
            for r in rows
        ]

    finally:
        conn.close()