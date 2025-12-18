import sqlite3
from datetime import datetime
from data.config import MANAGERS_BY_FACULTY
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "database", "bot.db")
from data.config import DB_PATH
# =============================
# 🔧 BAZA YARATISH
# =============================
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        # 1️⃣ O‘qituvchi / Tyutorlar jadvali
        c.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            user_id INTEGER PRIMARY KEY,
            fio TEXT,
            faculty TEXT,
            department TEXT,
            phone TEXT,
            role TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
        """)

        # 2️⃣ Talabalar jadvali
        c.execute("""
        CREATE TABLE IF NOT EXISTS students (
            user_id INTEGER PRIMARY KEY,
            fio TEXT,
            phone TEXT,
            faculty TEXT,
            edu_type TEXT,
            edu_form TEXT,
            course TEXT,
            student_group TEXT,
            passport TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        )
        """)

        # 3️⃣ Ro‘yxatdan o‘tish so‘rovlari
        c.execute("""
        CREATE TABLE IF NOT EXISTS register_requests (
            user_id INTEGER PRIMARY KEY,
            fio TEXT,
            phone TEXT,
            faculty TEXT,
            department TEXT,
            passport TEXT,
            role TEXT,
            edu_type TEXT,
            edu_form TEXT,
            course TEXT,
            student_group TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        """)

        # 4️⃣ Savollar jadvali
        c.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            fio TEXT,
            faculty TEXT,
            message_text TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            answered INTEGER DEFAULT 0
        )
        """)

        # 5️⃣ Javoblar jadvali
        c.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER,
            manager_id INTEGER,
            answer_text TEXT,
            answered_at TEXT DEFAULT (datetime('now','localtime'))
        )
        """)

        # 6️⃣ Baholar jadvali
        c.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER,
            manager_id INTEGER,
            question_id INTEGER,
            rating INTEGER,
            rated_at TEXT DEFAULT (datetime('now','localtime'))
        )
        """)
        conn.commit()
        print("✅ Barcha jadvallar tekshirildi yoki yaratildi.")

# =============================
# 📩 RO‘YXAT SO‘ROVINI SAQLASH
# =============================
def save_register_request(
    user_id,
    fio,
    phone,
    faculty,
    department=None,
    passport=None,
    role=None,
    edu_type=None,
    edu_form=None,
    course=None,
    student_group=None
):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        c.execute("""
            INSERT OR REPLACE INTO register_requests 
            (user_id, fio, phone, faculty, department, passport, role,
             edu_type, edu_form, course, student_group, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
        """, (
            user_id,
            fio,
            phone,
            faculty,
            department,
            passport,
            role,
            edu_type,
            edu_form,
            course,
            student_group
        ))

        conn.commit()


# =============================
# ✅ TASDIQLANGANLARNI ASOSIYGA YOZISH
# =============================
def approve_teacher_from_request(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        c.execute("SELECT fio, phone, faculty, department, passport, role FROM register_requests WHERE user_id = ?", (user_id,))
        row = c.fetchone()

        if not row:
            return False

        fio, phone, faculty, department, passport, role = row

        c.execute("""
        INSERT OR REPLACE INTO teachers
        (user_id, fio, phone, faculty, department, passport, role, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
        """,
        (user_id, fio, phone, faculty, department, passport, role))

        c.execute("DELETE FROM register_requests WHERE user_id = ?", (user_id,))
        conn.commit()

        return True


# =============================
# ❌ SO‘ROVNI O‘CHIRISH
# =============================
def delete_register_request(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM register_requests WHERE user_id = ?", (user_id,))
        conn.commit()


# =============================
# 📋 KUTILAYOTGAN SO‘ROVLAR
# =============================
def get_pending_requests():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM register_requests ORDER BY created_at DESC")
        return [dict(r) for r in c.fetchall()]

# ============================================================
# 🟢 register_requests → asosiy jadvallarga ko‘chiruvchi funksiya
# ============================================================
def move_request_to_main_tables(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()

        # Pending request olish
        c.execute("SELECT * FROM register_requests WHERE user_id=?", (user_id,))
        row = c.fetchone()

        if not row:
            return False

        (user_id, fio, phone, faculty, department, passport, role,
         edu_type, edu_form, course, student_group, created_at) = row

        # =========================
        #   O‘QITUVCHI
        # =========================
        if role == "O‘qituvchi":
            c.execute("""
                INSERT OR REPLACE INTO teachers
                (user_id, fio, faculty, department, phone, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now','localtime'))
            """, (user_id, fio, faculty, department, phone, role))

        # =========================
        #   TYUTOR
        # =========================
        elif role == "Tyutor":
            c.execute("""
                INSERT OR REPLACE INTO teachers
                (user_id, fio, faculty, department, phone, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, datetime('now','localtime'))
            """, (user_id, fio, faculty, None, phone, role))

        # =========================
        #   TALABA
        # =========================
        elif role == "Talaba":
            c.execute("""
                INSERT OR REPLACE INTO students
                (user_id, fio, phone, faculty, edu_type, edu_form,
                 course, student_group, passport, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now','localtime'))
            """, (
                user_id, fio, phone, faculty,
                edu_type, edu_form, course,
                student_group, passport
            ))

        # Pending so‘rovni o‘chirish
        c.execute("DELETE FROM register_requests WHERE user_id=?", (user_id,))

        conn.commit()
        return True

# =============================
# 👤 Foydalanuvchini olish
# =============================
def get_teacher(user_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM teachers WHERE user_id = ?", (user_id,))
        return c.fetchone()


# =============================
# 🔍 Ism bo‘yicha qidiruv
# =============================
def find_teachers_by_name(name):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM teachers WHERE fio LIKE ?", (f"%{name}%",))
        return [dict(r) for r in c.fetchall()]




def delete_teacher(user_id: int):
    """
    Foydalanuvchini bazadan o‘chiradi.
    Admin panelidagi 'O‘chirish' tugmasi uchun ishlatiladi.
    """
    import sqlite3
    conn = sqlite3.connect("database/bot.db")
    cur = conn.cursor()
    cur.execute("DELETE FROM teachers WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()
    print(f"🗑️ Foydalanuvchi {user_id} o‘chirildi.")


# =============================
# ⭐ Menejer bahosi
# =============================
def save_manager_rating(teacher_id, manager_id, question_id, rating):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
        INSERT INTO ratings (teacher_id, manager_id, question_id, rating, rated_at)
        VALUES (?, ?, ?, ?, ?)
        """, (teacher_id, manager_id, question_id, rating,
              datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

# =============================
# 🔍 Foydalanuvchi allaqachon baho berganmi?
# =============================
def user_already_rated(teacher_id: int, manager_id: int, question_id: int) -> bool:
    """
    Foydalanuvchi (teacher_id) shu menejerga (manager_id)
    shu savol (question_id) bo‘yicha allaqachon baho berganmi – tekshiradi.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM ratings
            WHERE teacher_id = ? AND manager_id = ? AND question_id = ?
        """, (teacher_id, manager_id, question_id))
        result = cur.fetchone()[0]
        return result > 0


import sqlite3
from data.config import DB_PATH

def get_manager_rating_table():
    import sqlite3
    from data.config import MANAGERS_BY_FACULTY, DB_PATH

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Barcha menejer ID larini yig‘ib olamiz
    manager_ids = set()
    manager_faculty = {}

    for faculty, fac in MANAGERS_BY_FACULTY.items():
        for mid in fac.get("student", []) + fac.get("teacher", []):
            manager_ids.add(mid)
            manager_faculty[mid] = faculty

    if not manager_ids:
        return []

    placeholders = ",".join("?" for _ in manager_ids)

    cur.execute(f"""
        SELECT
            q.manager_id                              AS manager_id,
            ROUND(AVG(r.rating), 2)                  AS avg_rating,
            COUNT(r.id)                              AS rating_count,
            SUM(CASE WHEN q.answered = 1 THEN 1 ELSE 0 END) AS answered_count,
            SUM(CASE WHEN q.answered = 0 THEN 1 ELSE 0 END) AS unanswered_count
        FROM questions q
        LEFT JOIN manager_ratings r ON r.manager_id = q.manager_id
        WHERE q.manager_id IN ({placeholders})
        GROUP BY q.manager_id
    """, list(manager_ids))

    rows = []
    for r in cur.fetchall():
        manager_id = r["manager_id"]

        # FIO olishga harakat qilamiz
        cur.execute("SELECT fio FROM teachers WHERE user_id=?", (manager_id,))
        t = cur.fetchone()
        fio = t["fio"] if t else f"Menejer ({manager_id})"

        rows.append({
            "manager_id": manager_id,
            "manager_name": fio,
            "faculty": manager_faculty.get(manager_id, "—"),
            "avg_rating": r["avg_rating"] or 0,
            "rating_count": r["rating_count"],
            "answered_count": r["answered_count"],
            "unanswered_count": r["unanswered_count"],
        })

    conn.close()
    return rows


def get_manager_rating_table_by_faculty():
    """
    7 ta fakultet bo‘yicha:
    - menejer(lar) FIO (teachers jadvalidan)
    - o‘rtacha reyting (manager_ratings)
    - answered / unanswered (questions)
    FAQAT MANAGERS_BY_FACULTY dagi IDlar bo‘yicha hisoblaydi.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    result = []

    for faculty_name, roles in MANAGERS_BY_FACULTY.items():
        manager_ids = list(set((roles.get("teacher") or []) + (roles.get("student") or [])))
        if not manager_ids:
            # fakultetda menejer yo‘q bo‘lsa ham jadvalda chiqsin
            result.append({
                "faculty": faculty_name,
                "manager_name": "—",
                "avg_rating": 0,
                "answered_count": 0,
                "unanswered_count": 0,
            })
            continue

        placeholders = ",".join(["?"] * len(manager_ids))

        # 1) Menejer(lar) FIO
        cur.execute(
            f"SELECT fio FROM teachers WHERE user_id IN ({placeholders})",
            manager_ids
        )
        names = [r["fio"] for r in cur.fetchall() if r["fio"]]
        manager_name = ", ".join(names) if names else ", ".join(map(str, manager_ids))

        # 2) Reyting (o‘rtacha)
        cur.execute(
            f"""
            SELECT ROUND(AVG(rating), 2) AS avg_rating
            FROM manager_ratings
            WHERE manager_id IN ({placeholders})
            """,
            manager_ids
        )
        avg_rating = cur.fetchone()["avg_rating"]
        avg_rating = avg_rating if avg_rating is not None else 0

        # 3) Savollar (answered / unanswered)
        cur.execute(
            f"""
            SELECT
                SUM(CASE WHEN answered=1 THEN 1 ELSE 0 END) AS answered_count,
                SUM(CASE WHEN answered=0 THEN 1 ELSE 0 END) AS unanswered_count
            FROM questions
            WHERE manager_id IN ({placeholders})
            """,
            manager_ids
        )
        row = cur.fetchone()
        answered_count = row["answered_count"] or 0
        unanswered_count = row["unanswered_count"] or 0

        result.append({
            "faculty": faculty_name,
            "manager_name": manager_name,
            "avg_rating": avg_rating,
            "answered_count": answered_count,
            "unanswered_count": unanswered_count,
        })

    conn.close()
    return result


# =============================
# 🏆 TOP menejerlar
# =============================
def get_top_managers(limit: int = 5):
    """
    Eng yuqori o'rtacha bahoga ega menejerlar.
    admin.py dagi 'TOP menejerlar' bo'limi uchun.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT
                manager_id,
                '' AS manager_name,
                '' AS faculty,
                ROUND(AVG(rating), 2) AS avg_rating
            FROM ratings
            GROUP BY manager_id
            HAVING COUNT(rating) > 0
            ORDER BY avg_rating DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        return [dict(r) for r in rows]


# =============================
# 🧩 Savolga javob berilganini belgilash
# =============================
def mark_question_answered(question_id):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "UPDATE questions SET answered = 1 WHERE id = ?",
            (question_id,)
        )
        conn.commit()


# =============================
# 🧾 Javobni saqlash
# =============================
def save_answer(question_id, manager_id, answer_text):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO answers(question_id, manager_id, answer_text)
        VALUES (?, ?, ?)
    """, (question_id, manager_id, answer_text))

    # ✅ mana shu MUHIM: questions.manager_id ni ham to‘ldirish
    cur.execute("""
        UPDATE questions
        SET manager_id = ?
        WHERE id = ?
    """, (manager_id, question_id))

    conn.commit()
    conn.close()

# =============================
# 📊 Excel eksport uchun savol-javoblar
# =============================
def fetch_answers_range(date_from: str, date_to: str):
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                q.id AS question_id,
                q.sender_id,
                q.fio,
                q.faculty,
                q.message_text,
                q.created_at,
                a.answer_text,
                a.manager_id,
                a.answered_at
            FROM questions q
            LEFT JOIN answers a ON q.id = a.question_id
            WHERE q.created_at BETWEEN ? AND ?
            ORDER BY q.created_at DESC
        """, (date_from, date_to))
        return [dict(row) for row in cur.fetchall()]

# =============================
# 🕓 So‘nggi yuborilgan savollarni olish
# =============================
def get_latest_questions(limit: int = 10):
    """
    So‘nggi yuborilgan savollarni olish uchun (rahbarlar paneli uchun).
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT id, sender_id, fio, faculty, message_text, created_at, answered
            FROM questions
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        return [dict(row) for row in rows]

# =============================
# 👥 Barcha foydalanuvchilarni (filtrlab) olish
# =============================
def get_all_teachers(faculty: str = None, department: str = None, fio: str = None, role: str = None):
    """
    Fakultet, kafedra yoki rol bo‘yicha foydalanuvchilarni chiqaradi.
    admin_message.py uchun ishlatiladi.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        query = "SELECT * FROM teachers WHERE 1=1"
        params = []

        if faculty:
            query += " AND faculty = ?"
            params.append(faculty)
        if department:
            query += " AND department = ?"
            params.append(department)
        if fio:
            query += " AND fio LIKE ?"
            params.append(f"%{fio}%")
        if role:
            query += " AND role = ?"
            params.append(role)

        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(r) for r in rows]

# =============================
# 🧱 Jadval mavjudligini tekshirish / yaratish
# =============================
def create_tables_if_not_exist():
    """
    Barcha kerakli jadvallar mavjudligini tekshiradi,
    bo‘lmasa avtomatik yaratadi.
    """
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        # O‘qituvchilar, tyutorlar, talabalar jadvali
        cur.execute("""
        CREATE TABLE IF NOT EXISTS teachers (
            user_id INTEGER PRIMARY KEY,
            fio TEXT,
            phone TEXT,
            faculty TEXT,
            department TEXT,
            passport TEXT,
            role TEXT,
            edu_type TEXT,
            edu_form TEXT,
            course TEXT,
            student_group TEXT,
            created_at TEXT
        );
        """)

        # Pending ro‘yxat so‘rovlari
        cur.execute("""
        CREATE TABLE IF NOT EXISTS register_requests (
            user_id INTEGER PRIMARY KEY,
            fio TEXT,
            phone TEXT,
            faculty TEXT,
            department TEXT,
            passport TEXT,
            role TEXT,
            edu_type TEXT,
            edu_form TEXT,
            course TEXT,
            student_group TEXT,
            created_at TEXT
        );
        """)

        # Savollar jadvali
        cur.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER,
            fio TEXT,
            faculty TEXT,
            message_text TEXT,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            answered INTEGER DEFAULT 0
        );
        """)

def create_manager_ratings_table():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS manager_ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            manager_id INTEGER,
            question_id INTEGER,
            rating INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


def create_orders_links_table():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        # Asosiy jadval (agar umuman bo‘lmasa, yaratadi)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                link TEXT,
                year TEXT,
                faculty TEXT,
                type TEXT,
                students TEXT,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

        # Mavjud ustunlarni tekshiramiz
        cur.execute("PRAGMA table_info(orders_links)")
        existing_cols = {row[1] for row in cur.fetchall()}

        # Etishmayotgan ustunlarni qo‘shamiz (agar eski jadval bo‘lsa)
        needed = {
            "year": "TEXT",
            "faculty": "TEXT",
            "type": "TEXT",
            "students": "TEXT",
        }

        for col_name, col_type in needed.items():
            if col_name not in existing_cols:
                cur.execute(f"ALTER TABLE orders_links ADD COLUMN {col_name} {col_type}")

        conn.commit()

def add_order_link(title, link, year, faculty, type, students):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO orders_links (title, link, year, faculty, type, students)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (title, link, year, faculty, type, students))
        conn.commit()

def get_order_links():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT title, link FROM orders_links ORDER BY id DESC")
        return cur.fetchall()

def save_commands_file(file_id: str):
    import sqlite3
    print(">>> save_commands_file ishlamoqda:", file_id)

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()

        # Jadvalni yaratamiz
        cur.execute("""
            CREATE TABLE IF NOT EXISTS commands_file (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_id TEXT,
                uploaded_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)

        # Eski fayllarni o'chiramiz (faqat 1 ta fayl)
        cur.execute("DELETE FROM commands_file")

        # Yangi faylni kiritamiz
        cur.execute("""
            INSERT INTO commands_file (file_id)
            VALUES (?)
        """, (file_id,))

        conn.commit()

        # Javoblar jadvali
        cur.execute("""
        CREATE TABLE IF NOT EXISTS answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_id INTEGER,
            manager_id INTEGER,
            answer_text TEXT,
            answered_at TEXT
        );
        """)

        # Reytinglar jadvali
        cur.execute("""
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER,
            manager_id INTEGER,
            question_id INTEGER,
            rating INTEGER,
            created_at TEXT
        );
        """)

        conn.commit()

    print("✅ Barcha jadvallar tekshirildi yoki yaratildi.")

# ============================
# 📘 BUYRUQLAR JADVALLARI
# ============================
def create_orders_table():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                file_id TEXT,
                uploaded_by INTEGER,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.commit()

def get_orders():
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("SELECT id, title, file_id, created_at FROM orders ORDER BY id DESC")
        return c.fetchall()

def update_order(order_id, new_title, new_file_id):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute("""
            UPDATE orders 
            SET title=?, file_id=?, created_at=datetime('now','localtime')
            WHERE id=?
        """, (new_title, new_file_id, order_id))
        conn.commit()

def get_commands_file():
    import sqlite3
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("SELECT file_id FROM commands_file ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()

        if row:
            return row["file_id"]
        return None

def commands_file_exists() -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM commands_file")
        return cur.fetchone()[0] > 0

# =============================
# 📘 Buyruqlar jadvali
# =============================
def init_orders_table():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                file_id TEXT,
                uploaded_by INTEGER,
                created_at TEXT DEFAULT (datetime('now','localtime'))
            );
        """)
        conn.commit()


# =============================
# ➕ Buyruq qo‘shish
# =============================
def add_order(title: str, file_id: str, uploaded_by: int):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO orders (title, file_id, uploaded_by, created_at)
            VALUES (?, ?, ?, datetime('now','localtime'))
        """, (title, file_id, uploaded_by))
        conn.commit()

# =============================
# 📄 Buyruqlar ro‘yxati
# =============================
def get_orders():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, file_id, created_at
            FROM orders
            ORDER BY created_at DESC
        """)
        return cur.fetchall()

def get_all_order_links():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT id, title, link, created_at
            FROM orders_links
            ORDER BY created_at DESC
        """)
        return [dict(row) for row in cur.fetchall()]

def search_orders_multi(year=None, faculty=None, type=None, lastname=None):
    """
    orders_links jadvalidan yil / fakultet / tur / familiya bo‘yicha filterlab qidiradi.
    """
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        query = """
            SELECT id, title, link, year, faculty, type, students, created_at
            FROM orders_links
            WHERE 1=1
        """
        params = []

        if year:
            query += " AND year = ?"
            params.append(year)
        if faculty:
            query += " AND faculty = ?"
            params.append(faculty)
        if type:
            query += " AND type = ?"
            params.append(type)
        if lastname:
            query += " AND students LIKE ?"
            params.append(f"%{lastname}%")

        query += " ORDER BY created_at DESC"
        cur.execute(query, params)
        return [dict(row) for row in cur.fetchall()]

# =============================
# ♻ Buyruqni yangilash
# =============================
def update_order(order_id: int, new_file_id: str):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            UPDATE orders
            SET file_id = ?, created_at = datetime('now','localtime')
            WHERE id = ?
        """, (new_file_id, order_id))
        conn.commit()

def get_filtered_teachers(data: dict):
    faculty = data.get("faculty")
    department = data.get("department")
    fio = data.get("fio")

    query = "SELECT * FROM teachers WHERE 1=1"
    params = []

    if faculty and faculty != "Barchasi":
        query += " AND faculty = ?"
        params.append(faculty)

    if department and department != "Barchasi":
        query += " AND department = ?"
        params.append(department)

    if fio and fio != "Barchasi":
        query += " AND fio LIKE ?"
        params.append(f"%{fio}%")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)

    return cur.fetchall()

def get_filtered_tutors(data: dict):
    faculty = data.get("faculty")
    fio = data.get("fio")

    query = "SELECT * FROM teachers WHERE role = 'tutor'"
    params = []

    if faculty and faculty != "Barchasi":
        query += " AND faculty = ?"
        params.append(faculty)

    if fio and fio != "Barchasi":
        query += " AND fio LIKE ?"
        params.append(f"%{fio}%")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)

    return cur.fetchall()


def get_filtered_students(data: dict):
    edu_type = data.get("edu_type")
    edu_form = data.get("edu_form")
    faculty = data.get("stu_faculty")
    course = data.get("course")
    group = data.get("group")
    fio = data.get("student_fio")

    query = "SELECT * FROM students WHERE 1=1"
    params = []

    if edu_type and edu_type != "all":
        query += " AND edu_type = ?"
        params.append(edu_type)

    if edu_form and edu_form != "Barchasi":
        query += " AND edu_form = ?"
        params.append(edu_form)

    if faculty and faculty != "Barchasi":
        query += " AND faculty = ?"
        params.append(faculty)

    if course and course != "all":
        query += " AND course = ?"
        params.append(course)

    if group and group != "Barchasi":
        query += " AND group_name = ?"
        params.append(group)

    if fio and fio != "Barchasi":
        query += " AND fio LIKE ?"
        params.append(f"%{fio}%")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)

    return cur.fetchall()

def get_faculty_teachers_stat():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT faculty, COUNT(*) AS total
        FROM teachers
        GROUP BY faculty
    """)

    return cur.fetchall()

def get_manager_name(manager_id: int):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT fio FROM teachers WHERE user_id = ?", (manager_id,))
    row = cur.fetchone()

    if row and row["fio"]:
        return row["fio"]

    # agar ustozlar jadvalida topilmasa, oddiy ID sifatida qaytaramiz
    return str(manager_id)

def search_users_by_fio_or_id(text: str, numeric_id: int = None):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    result = []

    # 🔎 O‘qituvchi / Tyutor
    cur.execute("""
        SELECT user_id, fio, faculty, 'teacher' AS category
        FROM teachers
        WHERE fio LIKE ? OR user_id = ?
    """, (f"%{text}%", numeric_id))
    result += cur.fetchall()

    # 🔎 Talaba
    cur.execute("""
        SELECT user_id, fio, faculty, 'student' AS category
        FROM students
        WHERE fio LIKE ? OR user_id = ?
    """, (f"%{text}%", numeric_id))
    result += cur.fetchall()

    conn.close()
    return result

def delete_user_by_id(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # O‘qituvchi / Tyutorni o‘chirish
    cur.execute("DELETE FROM teachers WHERE user_id = ?", (user_id,))

    # Talabani o‘chirish
    cur.execute("DELETE FROM students WHERE user_id = ?", (user_id,))

    conn.commit()
    conn.close()

def get_student(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM students WHERE user_id = ?", (user_id,))
    return cur.fetchone()


def get_question_by_id(question_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, sender_id, fio, faculty, message_text, created_at, answered
        FROM questions
        WHERE id = ?
    """, (question_id,))

    row = cur.fetchone()
    conn.close()
    return row

def save_question(sender_id, faculty, message_text, fio=None):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO questions(sender_id, faculty, message_text, fio, answered)
            VALUES (?, ?, ?, ?, 0)
        """, (sender_id, faculty, message_text, fio))
        conn.commit()
        return cur.lastrowid   # 🔴 MUHIM


    # ✅ MUHIM: yangi savol ID sini qaytaramiz
    return cur.lastrowid

def save_question_message_id(question_id: int, manager_id: int, message_id: int):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            """
            UPDATE questions
            SET manager_id = ?, manager_msg_id = ?
            WHERE id = ?
            """,
            (manager_id, message_id, question_id)
        )
        conn.commit()


# =============================
# 🚀 Dastur ishga tushganda
# =============================
init_db()
create_tables_if_not_exist()
create_orders_table()
create_orders_links_table()
create_manager_ratings_table()



