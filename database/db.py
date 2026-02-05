import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func, or_
from database.models import Teacher
from database.session import AsyncSessionLocal

from database.models import RegisterRequest
from .models import Base
from sqlalchemy import text

from .models import (
    Teacher,
    Student,
    RegisterRequest,
    Question,
    Answer,
    Rating,
    ManagerRating,
    Order,
    OrderLink,
    Manager,
    CommandsFile,
)
from data.config import MANAGERS_BY_FACULTY

from datetime import datetime
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL topilmadi")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

from contextlib import asynccontextmanager

@asynccontextmanager
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

def init_db():
    Base.metadata.create_all(bind=engine)

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
    db = SessionLocal()
    try:
        req = RegisterRequest(
            user_id=user_id,
            fio=fio,
            phone=phone,
            faculty=faculty,
            department=department,
            passport=passport,
            role=role,
            edu_type=edu_type,
            edu_form=edu_form,
            course=course,
            student_group=student_group,
            created_at=datetime.utcnow()
        )
        db.merge(req)   # INSERT OR REPLACE analogi
        db.commit()
    finally:
        db.close()

# =============================
# ✅ TASDIQLANGANLARNI ASOSIYGA YOZISH
# =============================

def approve_teacher_from_request(user_id: int) -> bool:
    db = SessionLocal()
    try:
        req = db.query(RegisterRequest).filter_by(user_id=user_id).first()
        if not req:
            return False

        teacher = Teacher(
            user_id=req.user_id,
            fio=req.fio,
            phone=req.phone,
            faculty=req.faculty,
            department=req.department,
            passport=req.passport,
            role=req.role,
            created_at=datetime.utcnow()
        )

        db.merge(teacher)
        db.delete(req)
        db.commit()
        return True
    finally:
        db.close()

# =============================
# ❌ SO‘ROVNI O‘CHIRISH
# =============================


def delete_register_request(user_id: int):
    db = SessionLocal()
    try:
        db.query(RegisterRequest).filter_by(user_id=user_id).delete()
        db.commit()
    finally:
        db.close()

# =============================
# 📋 KUTILAYOTGAN SO‘ROVLAR
# =============================
def get_pending_requests():
    db = SessionLocal()
    try:
        rows = (
            db.query(RegisterRequest)
            .order_by(RegisterRequest.created_at.desc())
            .all()
        )

        return [
            {
                "user_id": r.user_id,
                "fio": r.fio,
                "phone": r.phone,
                "faculty": r.faculty,
                "department": r.department,
                "passport": r.passport,
                "role": r.role,
                "edu_type": r.edu_type,
                "edu_form": r.edu_form,
                "course": r.course,
                "student_group": r.student_group,
                "created_at": r.created_at,
            }
            for r in rows
        ]
    finally:
        db.close()

# ============================================================
# 🟢 register_requests → asosiy jadvallarga ko‘chiruvchi funksiya
# ============================================================
from sqlalchemy.orm import Session
from database.models import RegisterRequest, Student, Teacher  # sizdagi nomlar mos bo‘lsa

# =====================================================
# ✅ SO‘ROVNI ASOSIY JADVALGA O‘TKAZISH
# =====================================================
def move_request_to_main_tables(user_id: int) -> bool:
    db = SessionLocal()
    try:
        req = db.execute(
            text("SELECT * FROM register_requests WHERE user_id = :uid"),
            {"uid": user_id}
        ).mappings().first()

        if not req:
            return False

        role = req["role"]

        if role == "Talaba":
            db.execute(
                text("""
                    INSERT INTO students
                    (user_id, fio, phone, faculty, edu_type, edu_form, course, student_group)
                    VALUES
                    (:user_id, :fio, :phone, :faculty, :edu_type, :edu_form, :course, :student_group)
                """),
                req
            )

        elif role in ("O‘qituvchi", "Tyutor"):
            db.execute(
                text("""
                    INSERT INTO teachers
                    (user_id, fio, phone, faculty, role)
                    VALUES
                    (:user_id, :fio, :phone, :faculty, :role)
                """),
                {
                    **req,
                    "role": "teacher" if role == "O‘qituvchi" else "tutor"
                }
            )

        db.execute(
            text("DELETE FROM register_requests WHERE user_id = :uid"),
            {"uid": user_id}
        )

        db.commit()
        return True

    except Exception as e:
        print("[APPROVE ERROR]", e)
        db.rollback()
        return False

    finally:
        db.close()

# =====================================================
# ❌ RO‘YXATDAN O‘TISH SO‘ROVINI RAD ETISH
# =====================================================
def reject_request(user_id: int) -> bool:
    db = SessionLocal()
    try:
        req = db.query(RegisterRequest).filter(
            RegisterRequest.user_id == user_id
        ).first()

        if not req:
            return False

        db.delete(req)
        db.commit()
        return True

    except Exception as e:
        db.rollback()
        print("[REJECT_REQUEST ERROR]", e)
        return False

    finally:
        db.close()

# =============================
# 🔍 Ism bo‘yicha qidiruv
# =============================

def find_teachers_by_name(name: str):
    db = SessionLocal()
    try:
        rows = db.query(Teacher).filter(
            Teacher.fio.ilike(f"%{name}%")
        ).all()

        return [
            {
                "user_id": t.user_id,
                "fio": t.fio,
                "faculty": t.faculty,
                "department": t.department,
                "phone": t.phone,
                "role": t.role,
            }
            for t in rows
        ]
    finally:
        db.close()


def delete_teacher(user_id: int):
    db = SessionLocal()
    try:
        db.query(Teacher).filter_by(user_id=user_id).delete()
        db.commit()
        print(f"🗑️ Foydalanuvchi {user_id} o‘chirildi.")
    finally:
        db.close()

# =============================
# ⭐ Menejer bahosi
# =============================
def save_manager_rating(teacher_id, manager_id, question_id, rating):
    db = SessionLocal()
    try:
        r = Rating(
            teacher_id=teacher_id,
            manager_id=manager_id,
            question_id=question_id,
            rating=rating,
            created_at=datetime.utcnow()
        )
        db.add(r)
        db.commit()
    finally:
        db.close()
# =============================
# 🔍 Foydalanuvchi allaqachon baho berganmi?
# =============================
def user_already_rated(teacher_id: int, manager_id: int, question_id: int) -> bool:
    db = SessionLocal()
    try:
        return db.query(Rating).filter_by(
            teacher_id=teacher_id,
            manager_id=manager_id,
            question_id=question_id
        ).count() > 0
    finally:
        db.close()

from sqlalchemy import func
from database.models import Rating, Question
from data.config import MANAGERS_BY_FACULTY

def get_manager_rating_table():
    db = SessionLocal()

    # 1️⃣ FaqAT fakultet menejerlarini yig‘amiz
    manager_ids = set()
    faculty_by_manager = {}

    for faculty, roles in MANAGERS_BY_FACULTY.items():
        for mid in (roles.get("teacher", []) + roles.get("student", [])):
            manager_ids.add(mid)
            faculty_by_manager[mid] = faculty

    if not manager_ids:
        return []

    # 2️⃣ FAQAT SHU menejerlar bo‘yicha reyting
    rows = (
        db.query(
            Rating.manager_id,
            func.count(func.distinct(Rating.question_id)).label("answered_count"),
            func.round(func.avg(Rating.rating), 2).label("avg_rating")
        )
        .filter(Rating.manager_id.in_(manager_ids))   # 🔥 ASOSIY FILTER
        .group_by(Rating.manager_id)
        .all()
    )

    result = []

    for r in rows:
        result.append({
            "manager_id": r.manager_id,
            "faculty": faculty_by_manager.get(r.manager_id, ""),
            "answered_count": r.answered_count,
            "unanswered_count": 0,
            "avg_rating": float(r.avg_rating or 0),
        })

    db.close()
    return result

def get_rating_table_by_faculty():
    db = SessionLocal()
    result = []

    for faculty_name, roles in MANAGERS_BY_FACULTY.items():
        manager_ids = list(set(
            (roles.get("teacher") or []) +
            (roles.get("student") or [])
        ))

        if not manager_ids:
            result.append({
                "faculty": faculty_name,
                "manager_name": "—",
                "avg_rating": 0,
                "answered_count": 0,
                "unanswered_count": 0,
            })
            continue

        # 👤 Menejer FIO
        names = db.query(Teacher.fio).filter(
            Teacher.user_id.in_(manager_ids)
        ).all()
        manager_name = ", ".join(n[0] for n in names if n[0]) or ", ".join(map(str, manager_ids))

        # ⭐ Reyting
        avg_rating = db.query(
            func.round(func.avg(Rating.rating), 2)
        ).filter(
            Rating.manager_id.in_(manager_ids)
        ).scalar() or 0

        # 📩 Savollar
        stats = db.query(
            func.sum(func.case((Question.answered == 1, 1), else_=0)),
            func.sum(func.case((Question.answered == 0, 1), else_=0))
        ).filter(
            Question.manager_id.in_(manager_ids)
        ).first()

        result.append({
            "faculty": faculty_name,
            "manager_name": manager_name,
            "avg_rating": float(avg_rating),
            "answered_count": int(stats[0] or 0),
            "unanswered_count": int(stats[1] or 0),
        })

    db.close()
    return result

# =============================
# 🏆 TOP menejerlar
# =============================
def get_top_managers(limit: int = 5):
    db = SessionLocal()

    rows = (
        db.query(
            Rating.manager_id,
            func.round(func.avg(Rating.rating), 2).label("avg_rating")
        )
        .group_by(Rating.manager_id)
        .having(func.count(Rating.rating) > 0)
        .order_by(func.avg(Rating.rating).desc())
        .limit(limit)
        .all()
    )

    db.close()

    return [
        {
            "manager_id": r.manager_id,
            "manager_name": "",
            "faculty": "",
            "avg_rating": float(r.avg_rating),
        }
        for r in rows
    ]

# =============================
# 🧩 Savolga javob berilganini belgilash
# =============================
def mark_question_answered(question_id: int):
    db = SessionLocal()
    db.query(Question).filter_by(id=question_id).update(
        {"answered": 1}
    )
    db.commit()
    db.close()

# =============================
# 🧾 Javobni saqlash
# =============================
from datetime import datetime
from database.models import Answer, Question  # sizdagi import yo‘liga moslang

def save_answer(question_id: int, manager_id: int, answer_text: str) -> bool:
    db = SessionLocal()
    try:
        # 1) Answer yozamiz (bu yerda Answer modelingizda qaysi ustunlar bor bo‘lsa, shularni ishlating)
        answer = Answer(
            question_id=question_id,
            manager_id=manager_id,
            answer_text=answer_text,
            created_at=datetime.utcnow()
        )
        db.add(answer)

        # 2) Question ni answered=True qilamiz
        # MUHIM: manager_id ni Question update ga YOZMAYMIZ (sizda u ustun yo‘q!)
        db.query(Question).filter(Question.id == question_id).update(
            {"answered": True},
            synchronize_session=False
        )

        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print("[DB save_answer ERROR]", e)
        return False
    finally:
        db.close()


# =============================
# 📊 Excel eksport uchun savol-javoblar
# =============================
def fetch_answers_range(date_from: str, date_to: str):
    db = SessionLocal()

    rows = (
        db.query(
            Question.id.label("question_id"),
            Question.sender_id,
            Question.fio,
            Question.faculty,
            Question.message_text,
            Question.created_at,
            Answer.answer_text,
            Answer.manager_id,
            Answer.answered_at
        )
        .outerjoin(Answer, Question.id == Answer.question_id)
        .filter(Question.created_at.between(date_from, date_to))
        .order_by(Question.created_at.desc())
        .all()
    )

    db.close()

    return [dict(r._mapping) for r in rows]

# =============================
# 🕓 So‘nggi yuborilgan savollarni olish
# =============================
def get_latest_questions(limit: int = 10):
    db = SessionLocal()
    rows = (
        db.query(Question)
        .order_by(Question.created_at.desc())
        .limit(limit)
        .all()
    )
    db.close()

    return [
        {
            "id": q.id,
            "sender_id": q.sender_id,
            "fio": q.fio,
            "faculty": q.faculty,
            "message_text": q.message_text,
            "created_at": q.created_at,
            "answered": q.answered,
        }
        for q in rows
    ]

# ==========================================
# 👔 RAHBAR UCHUN — faqat javob berilmagan savollar
# ==========================================
def get_latest_questions_for_manager(limit: int = 10):
    db = SessionLocal()
    rows = (
        db.query(Question)
        .filter(Question.answered == False)
        .order_by(Question.created_at.desc())
        .limit(limit)
        .all()
    )
    db.close()

    return [
        {
            "id": q.id,
            "sender_id": q.sender_id,
            "fio": q.fio,
            "faculty": q.faculty,
            "message_text": q.message_text,
            "created_at": q.created_at,
            "answered": q.answered,
        }
        for q in rows
    ]


# =============================
# 👥 Barcha foydalanuvchilarni (filtrlab) olish
# =============================
def get_all_teachers():
    db = SessionLocal()
    rows = db.query(Teacher).all()
    result = []
    for t in rows:
        result.append({
            "user_id": t.user_id,
            "fio": t.fio,
            "role": t.role,
            "faculty": getattr(t, "faculty", None),
        })
    db.close()
    return result


def add_order_link(title, link, year, faculty, type, students):
    db = SessionLocal()

    order = OrderLink(
        title=title,
        link=link,
        year=year,
        faculty=faculty,
        type=type,
        students=students,
    )

    db.add(order)
    db.commit()
    db.close()

def get_order_links():
    db = SessionLocal()

    rows = (
        db.query(OrderLink.title, OrderLink.link)
        .order_by(OrderLink.id.desc())
        .all()
    )

    db.close()
    return rows

def save_commands_file(file_id: str):
    print(">>> save_commands_file ishlamoqda:", file_id)

    db = SessionLocal()

    # eski faylni o‘chiramiz (faqat 1 ta saqlanadi)
    db.query(CommandsFile).delete()

    new_file = CommandsFile(file_id=file_id)
    db.add(new_file)

    db.commit()
    db.close()

    print("✅ commands_file yangilandi")

# ============================
# 📘 BUYRUQLAR JADVALLARI
# ============================
def get_orders():
    db = SessionLocal()

    rows = (
        db.query(Order.id, Order.title, Order.file_id, Order.created_at)
        .order_by(Order.created_at.desc())
        .all()
    )

    db.close()
    return rows

def add_order(title: str, file_id: str, uploaded_by: int):
    db = SessionLocal()

    order = Order(
        title=title,
        file_id=file_id,
        uploaded_by=uploaded_by
    )

    db.add(order)
    db.commit()
    db.close()

def update_order(order_id: int, new_title: str, new_file_id: str):
    db = SessionLocal()

    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        db.close()
        return False

    order.title = new_title
    order.file_id = new_file_id
    order.created_at = datetime.utcnow()

    db.commit()
    db.close()
    return True

def get_commands_file():
    db = SessionLocal()
    row = db.query(CommandsFile.file_id).order_by(CommandsFile.id.desc()).first()
    db.close()
    return row[0] if row else None

def commands_file_exists() -> bool:
    db = SessionLocal()
    exists = db.query(CommandsFile).count() > 0
    db.close()
    return exists

def get_all_order_links():
    db = SessionLocal()

    rows = (
        db.query(
            OrderLink.id,
            OrderLink.title,
            OrderLink.link,
            OrderLink.created_at
        )
        .order_by(OrderLink.created_at.desc())
        .all()
    )

    db.close()
    return rows

def search_orders_multi(faculty=None, type=None, lastname=None):
    db = SessionLocal()

    q = db.query(
        OrderLink.id,
        OrderLink.title,
        OrderLink.link,
        OrderLink.faculty,
        OrderLink.type,
        OrderLink.students,
    )

    if faculty:
        q = q.filter(OrderLink.faculty == faculty)

    if type:
        q = q.filter(OrderLink.type == type)

    rows = q.order_by(OrderLink.created_at.desc()).all()
    db.close()

    if not lastname:
        return rows

    normalized_input = normalize_text(lastname)
    filtered = []

    for r in rows:
        if not r.students:
            continue

        normalized_db = normalize_text(r.students)
        words = normalized_db.split(" ")

        if normalized_input in words:
            filtered.append(r)

    return filtered

# =============================
# ♻ Buyruqni yangilash
# =============================
def get_filtered_teachers(data: dict):
    db = SessionLocal()
    q = db.query(Teacher)

    faculty = data.get("faculty")
    department = data.get("department")
    fio = data.get("fio")

    if faculty and faculty != "Barchasi":
        q = q.filter(Teacher.faculty == faculty)

    if department and department != "Barchasi":
        q = q.filter(Teacher.department == department)

    if fio and fio != "Barchasi":
        q = q.filter(Teacher.fio.ilike(f"%{fio}%"))

    rows = q.all()
    db.close()
    return rows

def get_filtered_tutors(data: dict):
    db = SessionLocal()
    q = db.query(Teacher).filter(Teacher.role == "tutor")

    faculty = data.get("faculty")
    fio = data.get("fio")

    if faculty and faculty != "Barchasi":
        q = q.filter(Teacher.faculty == faculty)

    if fio and fio != "Barchasi":
        q = q.filter(Teacher.fio.ilike(f"%{fio}%"))

    rows = q.all()
    db.close()
    return rows

def get_filtered_students(data: dict):
    db = SessionLocal()
    q = db.query(Student)

    if data.get("edu_type") and data["edu_type"] != "all":
        q = q.filter(Student.edu_type == data["edu_type"])

    if data.get("edu_form") and data["edu_form"] != "Barchasi":
        q = q.filter(Student.edu_form == data["edu_form"])

    if data.get("stu_faculty") and data["stu_faculty"] != "Barchasi":
        q = q.filter(Student.faculty == data["stu_faculty"])

    if data.get("course") and data["course"] != "all":
        q = q.filter(Student.course == data["course"])

    if data.get("group") and data["group"] != "Barchasi":
        q = q.filter(Student.student_group == data["group"])

    if data.get("student_fio") and data["student_fio"] != "Barchasi":
        q = q.filter(Student.fio.ilike(f"%{data['student_fio']}%"))

    rows = q.all()
    db.close()
    return rows

def get_faculty_teachers_stat():
    db = SessionLocal()
    try:
        rows = (
            db.query(
                Teacher.faculty,
                func.count(Teacher.user_id).label("total")
            )
            .group_by(Teacher.faculty)
            .all()
        )
        return rows
    finally:
        db.close()

def get_manager_name(manager_id: int) -> str:
    db = SessionLocal()
    try:
        teacher = db.query(Teacher).filter(Teacher.user_id == manager_id).first()
        return teacher.fio if teacher else str(manager_id)
    finally:
        db.close()

def save_manager_name(user_id: int, full_name: str):
    db = SessionLocal()
    try:
        manager = db.query(Manager).filter(Manager.user_id == user_id).first()
        if manager:
            manager.full_name = full_name
        else:
            manager = Manager(user_id=user_id, full_name=full_name)
            db.add(manager)
        db.commit()
    finally:
        db.close()

def search_users_by_fio_or_id(text: str, numeric_id: int = None):
    db = SessionLocal()
    try:
        result = []

        teachers = db.query(Teacher).filter(
            or_(
                Teacher.fio.ilike(f"%{text}%"),
                Teacher.user_id == numeric_id
            )
        ).all()

        for t in teachers:
            result.append({
                "user_id": t.user_id,
                "fio": t.fio,
                "faculty": t.faculty,
                "category": "teacher"
            })

        students = db.query(Student).filter(
            or_(
                Student.fio.ilike(f"%{text}%"),
                Student.user_id == numeric_id
            )
        ).all()

        for s in students:
            result.append({
                "user_id": s.user_id,
                "fio": s.fio,
                "faculty": s.faculty,
                "category": "student"
            })

        return result
    finally:
        db.close()

def delete_user_by_id(user_id: int):
    db = SessionLocal()
    try:
        db.query(Teacher).filter(Teacher.user_id == user_id).delete()
        db.query(Student).filter(Student.user_id == user_id).delete()
        db.commit()
    finally:
        db.close()

def get_student(user_id: int):
    db = SessionLocal()
    try:
        return db.query(Student).filter(
            Student.user_id == user_id
        ).first()
    finally:
        db.close()

# =====================================================
# 👨‍🏫 O‘QITUVCHINI OLISH
# =====================================================
def get_teacher(user_id: int):
    db = SessionLocal()
    try:
        return db.query(Teacher).filter(
            Teacher.user_id == user_id
        ).first()
    finally:
        db.close()

def get_question_by_id(question_id: int):
    db = SessionLocal()
    try:
        return db.query(Question).filter(Question.id == question_id).first()
    finally:
        db.close()

from database.db import SessionLocal  # sizda SessionLocal qayerda bo‘lsa o‘sha import
from database.models import Question

def save_question(sender_id: int, sender_role: str, faculty: str, message_text: str, fio: str):
    db = SessionLocal()
    try:
        q = Question(
            sender_id=sender_id,
            sender_role=sender_role,   # <-- MUHIM
            faculty=faculty,
            message_text=message_text,
            fio=fio,
            answered=False
        )
        db.add(q)
        db.commit()
        db.refresh(q)
        return q.id
    except Exception as e:
        db.rollback()
        print("[DB save_question ERROR]", e)
        return None
    finally:
        db.close()

def save_question_message_id(question_id: int, manager_id: int, message_id: int):
    db = SessionLocal()
    try:
        q = db.query(Question).filter(Question.id == question_id).first()
        if not q:
            return False

        q.manager_id = manager_id
        q.manager_msg_id = message_id
        db.commit()
        return True
    finally:
        db.close()

def get_manager_fio(manager_id: int) -> str:
    db = SessionLocal()
    try:
        teacher = db.query(Teacher).filter(Teacher.user_id == manager_id).first()
        return teacher.fio if teacher else "Noma’lum menejer"
    finally:
        db.close()

from sqlalchemy import select

async def get_user_by_id(user_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

# =============================
# ❌ HAVOLALI BUYRUQLARNI O‘CHIRISH (ADMIN) — OrderLink
# =============================

def search_order_links_for_delete(query: str):
    db = SessionLocal()
    try:
        q = db.query(OrderLink)

        # ID bo‘lsa
        if query.isdigit():
            return q.filter(OrderLink.id == int(query)).all()

        # title bo‘yicha
        return q.filter(OrderLink.title.ilike(f"%{query}%")).order_by(OrderLink.id.desc()).all()
    finally:
        db.close()


def delete_order_link_by_id(order_id: int) -> bool:
    db = SessionLocal()
    try:
        order = db.query(OrderLink).filter(OrderLink.id == order_id).first()
        if not order:
            return False

        db.delete(order)
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        print("[DELETE ORDER LINK ERROR]", e)
        return False
    finally:
        db.close()

import re

def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = text.lower()
    text = (
        text.replace("‘", "'")
            .replace("’", "'")
            .replace("ʻ", "'")
            .replace("ʼ", "'")
    )

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def search_orders_by_full_fio(faculty: str, fio: str):
    db = SessionLocal()

    input_words = normalize_text(fio).split()

    rows = (
        db.query(
            OrderLink.id,
            OrderLink.title,
            OrderLink.link,
            OrderLink.students,
        )
        .filter(OrderLink.faculty == faculty)
        .order_by(OrderLink.created_at.desc())
        .all()
    )

    db.close()

    result = []

    for r in rows:
        if not r.students:
            continue

        db_words = normalize_text(r.students).split()

        # 👉 inputdagi HAR BIR so‘z DB dagi so‘zlar ichida bo‘lishi shart
        if all(word in db_words for word in input_words):
            result.append(r)

    return result

# =============================
# 🚀 Dastur ishga tushganda
# =============================
def init_db():
    Base.metadata.create_all(bind=engine)
    print("✅ PostgreSQL jadvallar tayyor")


