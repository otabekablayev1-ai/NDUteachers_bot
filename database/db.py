import os
from datetime import datetime

from sqlalchemy import (
    select,
    delete,
    update,
    func,
)
from database.engine import engine
from database.session import AsyncSessionLocal
from database.models import (
    Base,
    Teacher,
    Student,
    RegisterRequest,
    Question,
    Answer,
    Rating,
    Manager,
    Order,
    OrderLink,
    CommandsFile,
)
from data.config import MANAGERS_BY_FACULTY

# =====================================================
# 🔧 DATABASE URL CHECK
# =====================================================
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("❌ DATABASE_URL topilmadi")

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace(
        "postgres://", "postgresql+asyncpg://", 1
    )

# =====================================================
# 🚀 INIT DB
# =====================================================
async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# =====================================================
# 📩 RO‘YXAT SO‘ROVINI SAQLASH
# =====================================================
async def save_register_request(
    user_id: int,
    fio: str,
    phone: str,
    faculty: str,
    department: str | None = None,
    passport: str | None = None,
    role: str | None = None,
    edu_type: str | None = None,
    edu_form: str | None = None,
    course: str | None = None,
    student_group: str | None = None,
) -> None:

    async with AsyncSessionLocal() as session:
        try:
            # 🔎 Avval mavjudligini tekshiramiz
            result = await session.execute(
                select(RegisterRequest).where(RegisterRequest.user_id == user_id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                # 🔁 UPDATE
                existing.fio = fio
                existing.phone = phone
                existing.faculty = faculty
                existing.department = department
                existing.passport = passport
                existing.role = role
                existing.edu_type = edu_type
                existing.edu_form = edu_form
                existing.course = course
                existing.student_group = student_group
                existing.created_at = datetime.utcnow()

            else:
                # ➕ INSERT
                session.add(
                    RegisterRequest(
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
                        created_at=datetime.utcnow(),
                    )
                )

            await session.commit()

        except Exception as e:
            await session.rollback()
            print("REGISTER SAVE ERROR:", e)
            raise
# =====================================================
# ✅ TASDIQLANGANLARNI ASOSIYGA YOZISH (TEACHER)
# =====================================================
async def approve_teacher_from_request(user_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        try:
            req = await session.scalar(
                select(RegisterRequest).where(
                    RegisterRequest.user_id == user_id
                )
            )

            if not req:
                return False

            session.add(
                Teacher(
                    user_id=req.user_id,
                    fio=req.fio,
                    phone=req.phone,
                    faculty=req.faculty,
                    department=req.department,
                    passport=req.passport,
                    role=req.role,
                    created_at=datetime.utcnow(),
                )
            )

            await session.delete(req)
            await session.commit()
            return True

        except Exception:
            await session.rollback()
            return False

# =====================================================
# ❌ SO‘ROVNI O‘CHIRISH
# =====================================================
async def delete_register_request(user_id: int) -> None:
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(
                delete(RegisterRequest).where(
                    RegisterRequest.user_id == user_id
                )
            )
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# =====================================================
# 📋 KUTILAYOTGAN SO‘ROVLAR
# =====================================================
async def get_pending_requests() -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(RegisterRequest)
            .order_by(RegisterRequest.created_at.desc())
        )
        rows = result.scalars().all()

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

# =====================================================
# ✅ SO‘ROVNI ASOSIY JADVALGA O‘TKAZISH
# =====================================================
async def move_request_to_main_tables(user_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                select(RegisterRequest).where(
                    RegisterRequest.user_id == user_id
                )
            )
            req = result.scalar_one_or_none()

            if not req:
                return False

            if req.role == "Talaba":
                session.add(
                    Student(
                        user_id=req.user_id,
                        fio=req.fio,
                        phone=req.phone,
                        faculty=req.faculty,
                        edu_type=req.edu_type,
                        edu_form=req.edu_form,
                        course=req.course,
                        student_group=req.student_group,
                    )
                )

            elif req.role in ("O‘qituvchi", "Tyutor"):
                session.add(
                    Teacher(
                        user_id=req.user_id,
                        fio=req.fio,
                        phone=req.phone,
                        faculty=req.faculty,
                        role="teacher" if req.role == "O‘qituvchi" else "tutor",
                    )
                )

            await session.delete(req)
            await session.commit()
            return True

        except Exception as e:
            print("[APPROVE ERROR]", e)
            await session.rollback()
            return False
# =====================================================
# ❌ RO‘YXATDAN O‘TISH SO‘ROVINI RAD ETISH
# =====================================================
async def reject_request(user_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        try:
            req = await session.get(RegisterRequest, user_id)

            if not req:
                return False

            await session.delete(req)
            await session.commit()
            return True

        except Exception:
            await session.rollback()
            return False
# =====================================================
# 🔍 O‘QITUVCHILARNI ISM BO‘YICHA QIDIRISH
# =====================================================
async def find_teachers_by_name(name: str) -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Teacher).where(
                Teacher.fio.ilike(f"%{name}%")
            )
        )
        teachers = result.scalars().all()

    return [
        {
            "user_id": t.user_id,
            "fio": t.fio,
            "faculty": t.faculty,
            "department": t.department,
            "phone": t.phone,
            "role": t.role,
        }
        for t in teachers
    ]


# =====================================================
# 🗑️ O‘QITUVCHINI O‘CHIRISH
# =====================================================
async def delete_teacher(user_id: int) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(Teacher).where(Teacher.user_id == user_id)
        )
        await session.commit()


# =====================================================
# ⭐ MENEJER BAHOSINI SAQLASH
# =====================================================
async def save_manager_rating(
    teacher_id: int,
    manager_id: int,
    question_id: int,
    rating: int,
) -> None:
    async with AsyncSessionLocal() as session:
        session.add(
            Rating(
                teacher_id=teacher_id,
                manager_id=manager_id,
                question_id=question_id,
                rating=rating,
                created_at=datetime.utcnow(),
            )
        )
        await session.commit()


# =====================================================
# 🔍 FOYDALANUVCHI OLDIN BAHO BERGANMI?
# =====================================================
async def user_already_rated(
    teacher_id: int,
    manager_id: int,
    question_id: int,
) -> bool:
    async with AsyncSessionLocal() as session:
        count = await session.scalar(
            select(func.count(Rating.id)).where(
                Rating.teacher_id == teacher_id,
                Rating.manager_id == manager_id,
                Rating.question_id == question_id,
            )
        )
        return count > 0


# =====================================================
# 📊 MENEJERLAR BAHO JADVALI
# =====================================================


async def get_manager_rating_table() -> list[dict]:
    manager_ids: set[int] = set()
    faculty_by_manager: dict[int, str] = {}

    for faculty, roles in MANAGERS_BY_FACULTY.items():
        ids = (roles.get("teacher") or []) + (roles.get("student") or [])
        for mid in ids:
            manager_ids.add(mid)
            faculty_by_manager[mid] = faculty

    if not manager_ids:
        return []

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(
                Rating.manager_id,
                func.count(Rating.id).label("answered_count"),
                func.round(func.avg(Rating.rating), 2).label("avg_rating"),
            )
            .where(Rating.manager_id.in_(manager_ids))
            .group_by(Rating.manager_id)
        )

        rows = result.all()

    table = [
        {
            "manager_id": r.manager_id,
            "faculty": faculty_by_manager.get(r.manager_id, ""),
            "answered_count": r.answered_count or 0,
            "unanswered_count": 0,
            "avg_rating": float(r.avg_rating or 0),
        }
        for r in rows
    ]

    # Reyting bo‘yicha sort
    table.sort(key=lambda x: x["avg_rating"], reverse=True)

    return table


# =====================================================
# 📊 FAKULTET BO‘YICHA REYTING
# =====================================================

async def get_rating_table_by_faculty() -> list[dict]:
    result = []

    async with AsyncSessionLocal() as session:

        rating_data = await session.execute(
            select(
                Rating.manager_id,
                func.count(Rating.id).label("answered_count"),
                func.round(func.avg(Rating.rating), 2).label("avg_rating"),
            )
            .group_by(Rating.manager_id)
        )

        rating_map = {
            r.manager_id: {
                "answered_count": r.answered_count or 0,
                "avg_rating": float(r.avg_rating or 0),
            }
            for r in rating_data
        }

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

            names_res = await session.execute(
                select(Teacher.fio)
                .where(Teacher.user_id.in_(manager_ids))
            )

            names = names_res.scalars().all()
            manager_name = ", ".join(n for n in names if n) \
                or ", ".join(map(str, manager_ids))

            total_answered = sum(
                rating_map.get(mid, {}).get("answered_count", 0)
                for mid in manager_ids
            )

            avg_values = [
                rating_map.get(mid, {}).get("avg_rating", 0)
                for mid in manager_ids
                if mid in rating_map
            ]

            faculty_avg = round(sum(avg_values) / len(avg_values), 2) \
                if avg_values else 0

            result.append({
                "faculty": faculty_name,
                "manager_name": manager_name,
                "avg_rating": faculty_avg,
                "answered_count": total_answered,
                "unanswered_count": 0,
            })

    result.sort(key=lambda x: x["avg_rating"], reverse=True)

    return result
# =============================
# 🏆 TOP menejerlar
# =============================
async def get_top_managers(limit: int = 5) -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(
                Rating.manager_id.label("manager_id"),
                func.round(func.avg(Rating.rating), 2).label("avg_rating"),
            )
            .group_by(Rating.manager_id)
            .order_by(func.avg(Rating.rating).desc())
            .limit(limit)
        )

        rows = result.mappings().all()

    return [
        {
            "manager_id": r["manager_id"],
            "manager_name": "",
            "faculty": "",
            "avg_rating": float(r["avg_rating"] or 0),
        }
        for r in rows
    ]
# =============================
# 🧩 Savolga javob berilganini belgilash
# =============================
async def mark_question_answered(question_id: int):
    async with AsyncSessionLocal() as session:
        await session.execute(
            update(Question)
            .where(Question.id == question_id)
            .values(answered=True)
        )
        await session.commit()

# =============================
# 🧾 Javobni saqlash
# =============================
async def save_answer(question_id: int, manager_id: int, answer_text: str) -> bool:
    async with AsyncSessionLocal() as session:
        try:
            ans = Answer(
                question_id=question_id,
                manager_id=manager_id,
                answer_text=answer_text,
                created_at=datetime.utcnow()
            )
            session.add(ans)

            await session.execute(
                update(Question)
                .where(Question.id == question_id)
                .values(answered=True)
            )

            await session.commit()
            return True
        except Exception as e:
            await session.rollback()
            print("[DB save_answer ERROR]", e)
            return False

# ==========================================
# 👔 RAHBAR UCHUN — javob berilmagan savollar
# ==========================================
async def get_latest_questions_for_manager(
    manager_id: int,
    limit: int = 10,
):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Question)
            .where(
                Question.answered.is_(False),
                Question.manager_id == manager_id
            )
            .order_by(Question.created_at.desc())
            .limit(limit)
        )
        questions = result.scalars().all()

    return [
        {
            "id": q.id,
            "fio": q.fio,
            "faculty": q.faculty,
            "message_text": q.message_text,
            "created_at": q.created_at,
            "answered": q.answered,
        }
        for q in questions
    ]

# =============================
# 👥 Barcha o‘qituvchilar
# =============================
async def get_all_teachers() -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Teacher))
        teachers = result.scalars().all()

    return [
        {
            "user_id": t.user_id,
            "fio": t.fio,
            "role": t.role,
            "faculty": t.faculty,
        }
        for t in teachers
    ]

# =============================
# ➕ OrderLink qo‘shish
# =============================
async def add_order_link(
    title: str,
    link: str,
    year: str,
    faculty: str,
    type: str,
    students_raw: str,
    students_search: str,
):
    async with AsyncSessionLocal() as session:
        order = OrderLink(
            title=title,
            link=link,
            year=year,
            faculty=faculty,
            type=type,
            students_raw=students_raw,
            students_search=students_search,
            created_at=datetime.utcnow(),
        )
        session.add(order)
        await session.commit()

# =============================
# 📎 OrderLink ro‘yxati
# =============================
async def get_order_links():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(OrderLink.title, OrderLink.link)
            .order_by(OrderLink.id.desc())
        )
        return result.all()


async def save_commands_file(file_id: str) -> None:
    async with AsyncSessionLocal() as session:
        # eski faylni o‘chiramiz (faqat 1 ta saqlanadi)
        await session.execute(delete(CommandsFile))

        session.add(
            CommandsFile(file_id=file_id)
        )

        await session.commit()
async def get_commands_file() -> str | None:
     async with AsyncSessionLocal() as session:
        return await session.scalar(
            select(CommandsFile.file_id)
            .order_by(CommandsFile.id.desc())
        )

async def commands_file_exists() -> bool:
    async with AsyncSessionLocal() as session:
        count = await session.scalar(
            select(func.count(CommandsFile.id))
        )
        return count > 0
# =============================
# 📘 BUYRUQLAR
# =============================
async def get_orders():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(
                Order.id,
                Order.title,
                Order.file_id,
                Order.created_at,
            )
            .order_by(Order.created_at.desc())
        )
        return result.all()


async def add_order(
    title: str,
    file_id: str,
    uploaded_by: int,
) -> None:
    async with AsyncSessionLocal() as session:
        session.add(
            Order(
                title=title,
                file_id=file_id,
                uploaded_by=uploaded_by,
            )
        )
        await session.commit()

async def update_order(
    order_id: int,
    new_title: str,
    new_file_id: str,
) -> bool:
    async with AsyncSessionLocal() as session:
        order = await session.scalar(
            select(Order).where(Order.id == order_id)
        )
        if not order:
            return False

        order.title = new_title
        order.file_id = new_file_id
        order.created_at = datetime.utcnow()

        await session.commit()
        return True


# =============================
# 📚 OrderLink ro‘yxati (to‘liq)
# =============================
async def get_all_order_links():
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(
                OrderLink.id,
                OrderLink.title,
                OrderLink.link,
                OrderLink.created_at,
            )
            .order_by(OrderLink.created_at.desc())
        )
        return result.all()

# =============================
# 🔎 Filtrlash — Teachers / Tutors / Students
# =============================

async def get_filtered_teachers(data: dict):
    async with AsyncSessionLocal() as session:
        stmt = select(Teacher)

        if data.get("faculty") not in (None, "Barchasi"):
            stmt = stmt.where(Teacher.faculty == data["faculty"])

        if data.get("department") not in (None, "Barchasi"):
            stmt = stmt.where(Teacher.department == data["department"])

        if data.get("fio") not in (None, "Barchasi"):
            stmt = stmt.where(Teacher.fio.ilike(f"%{data['fio']}%"))

        result = await session.execute(stmt)
        return result.scalars().all()


async def get_filtered_tutors(data: dict):
    async with AsyncSessionLocal() as session:
        stmt = select(Teacher).where(Teacher.role == "tutor")

        if data.get("faculty") not in (None, "Barchasi"):
            stmt = stmt.where(Teacher.faculty == data["faculty"])

        if data.get("fio") not in (None, "Barchasi"):
            stmt = stmt.where(Teacher.fio.ilike(f"%{data['fio']}%"))

        result = await session.execute(stmt)
        return result.scalars().all()


async def get_filtered_students(data: dict):
    async with AsyncSessionLocal() as session:
        stmt = select(Student)

        if data.get("edu_type") not in (None, "all"):
            stmt = stmt.where(Student.edu_type == data["edu_type"])

        if data.get("edu_form") not in (None, "Barchasi"):
            stmt = stmt.where(Student.edu_form == data["edu_form"])

        if data.get("stu_faculty") not in (None, "Barchasi"):
            stmt = stmt.where(Student.faculty == data["stu_faculty"])

        if data.get("course") not in (None, "all"):
            stmt = stmt.where(Student.course == data["course"])

        if data.get("group") not in (None, "Barchasi"):
            stmt = stmt.where(Student.student_group == data["group"])

        if data.get("student_fio") not in (None, "Barchasi"):
            stmt = stmt.where(
                Student.fio.ilike(f"%{data['student_fio']}%")
            )

        result = await session.execute(stmt)
        return result.scalars().all()

# =============================
# 👤 Menejerlar / foydalanuvchilar
# =============================
async def get_manager_name(manager_id: int) -> str:
    async with AsyncSessionLocal() as session:
        fio = await session.scalar(
            select(Teacher.fio).where(
                Teacher.user_id == manager_id
            )
        )
        return fio or str(manager_id)


async def save_manager_name(
    user_id: int,
    full_name: str,
) -> None:
    async with AsyncSessionLocal() as session:
        manager = await session.scalar(
            select(Manager).where(Manager.user_id == user_id)
        )
        if manager:
            manager.full_name = full_name
        else:
            session.add(
                Manager(user_id=user_id, full_name=full_name)
            )
        await session.commit()

# =============================
# 🗑️ Foydalanuvchini o‘chirish
# =============================
async def delete_user_by_id(user_id: int) -> None:
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(Teacher).where(Teacher.user_id == user_id)
        )
        await session.execute(
            delete(Student).where(Student.user_id == user_id)
        )
        await session.commit()


# =============================
# 🎓 Student / Teacher / Question
# =============================
async def get_student(user_id: int):
    async with AsyncSessionLocal() as session:
        return await session.scalar(
            select(Student).where(Student.user_id == user_id)
        )


async def get_teacher(user_id: int):
    async with AsyncSessionLocal() as session:
        return await session.scalar(
            select(Teacher).where(Teacher.user_id == user_id)
        )


async def get_question_by_id(question_id: int):
    async with AsyncSessionLocal() as session:
        return await session.scalar(
            select(Question).where(Question.id == question_id)
        )


async def save_question(
    sender_id: int,
    sender_role: str,
    faculty: str,
    message_text: str,
    fio: str,
) -> int | None:
    async with AsyncSessionLocal() as session:
        try:
            q = Question(
                sender_id=sender_id,
                sender_role=sender_role,
                faculty=faculty,
                message_text=message_text,
                fio=fio,
                answered=False,
            )
            session.add(q)
            await session.commit()
            await session.refresh(q)
            return q.id
        except Exception:
            await session.rollback()
            return None


async def save_question_message_id(
    question_id: int,
    manager_id: int,
    message_id: int,
) -> bool:
    async with AsyncSessionLocal() as session:
        q = await session.scalar(
            select(Question).where(Question.id == question_id)
        )
        if not q:
            return False

        q.manager_id = manager_id
        q.manager_msg_id = message_id
        await session.commit()
        return True

async def fetch_answers_range(
    date_from: str,
    date_to: str,
):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(
                Question.id.label("question_id"),
                Question.sender_id,
                Question.fio,
                Question.faculty,
                Question.message_text,
                Question.created_at,
                Answer.answer_text,
                Answer.manager_id,
                Answer.answered_at,
            )
            .outerjoin(
                Answer,
                Question.id == Answer.question_id,
            )
            .where(
                Question.created_at.between(
                    date_from,
                    date_to,
                )
            )
            .order_by(Question.created_at.desc())
        )

        rows = result.mappings().all()

    return rows

async def get_manager_fio(manager_id: int) -> str:
    async with AsyncSessionLocal() as session:
        fio = await session.scalar(
            select(Teacher.fio).where(
                Teacher.user_id == manager_id
            )
        )
        return fio or "Noma’lum menejer"

# =============================
# 🔍 OrderLink — PROFESSIONAL qidiruv
# =============================
from sqlalchemy import or_
from database.utils import normalize_text

async def search_orders_multi(
    faculty: str | None = None,
    type: str | None = None,
    fio: str | None = None,
):
    async with AsyncSessionLocal() as session:
        stmt = select(
            OrderLink.id,
            OrderLink.title,
            OrderLink.link,
            OrderLink.faculty,
            OrderLink.type,
            OrderLink.students_raw,
            OrderLink.students_search,
            OrderLink.created_at,
        )

        if faculty:
            stmt = stmt.where(OrderLink.faculty == faculty)

        if type:
            stmt = stmt.where(OrderLink.type == type)

        if fio:
            search_text = normalize_text(fio)
            stmt = stmt.where(
                OrderLink.students_search.ilike(f"%{search_text}%")
            )

        stmt = stmt.order_by(OrderLink.created_at.desc())

        result = await session.execute(stmt)
        return result.all()

# =============================
# ❌ OrderLink (ADMIN) — o‘chirish
# =============================
async def search_order_links_for_delete(query: str):
    async with AsyncSessionLocal() as session:
        stmt = select(OrderLink)

        if query.isdigit():
            stmt = stmt.where(OrderLink.id == int(query))
        else:
            stmt = stmt.where(
                OrderLink.title.ilike(f"%{query}%")
            )

        result = await session.execute(
            stmt.order_by(OrderLink.id.desc())
        )
        return result.scalars().all()


async def delete_order_link_by_id(order_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        order = await session.scalar(
            select(OrderLink).where(OrderLink.id == order_id)
        )
        if not order:
            return False

        await session.delete(order)
        await session.commit()
        return True


async def search_users_by_fio_or_id(
    text: str,
    numeric_id: int | None = None,
):
    async with AsyncSessionLocal() as session:
        teachers = (await session.execute(
            select(Teacher).where(
                or_(
                    Teacher.fio.ilike(f"%{text}%"),
                    Teacher.user_id == numeric_id,
                )
            )
        )).scalars().all()

        students = (await session.execute(
            select(Student).where(
                or_(
                    Student.fio.ilike(f"%{text}%"),
                    Student.user_id == numeric_id,
                )
            )
        )).scalars().all()

    return teachers + students

async def search_orders_by_full_fio(
    faculty: str | None,
    fio_query: str,
):
    async with AsyncSessionLocal() as session:
        stmt = select(
            OrderLink.id,
            OrderLink.title,
            OrderLink.link,
            OrderLink.faculty,
            OrderLink.students_raw,
            OrderLink.students_search,
            OrderLink.created_at,
        ).order_by(OrderLink.created_at.desc())

        if faculty:
            stmt = stmt.where(OrderLink.faculty == faculty)

        result = await session.execute(stmt)
        rows = result.all()

    query_words = normalize_text(fio_query).split()
    filtered = []

    for r in rows:
        if not r.students_search:
            continue

        student_words = normalize_text(r.students_search).split()

        if all(word in student_words for word in query_words):
            filtered.append(r)

    return filtered

# =============================
# 📊 Statistikalar
# =============================
# =============================
# 🏫 Fakultetlar bo‘yicha umumiy statistika
# (Teacher + Tutor + Student)
# =============================
async def get_faculty_full_statistics():
    async with AsyncSessionLocal() as session:

        # Teacher + Tutor (bitta jadvalda)
        teachers_result = await session.execute(
            select(
                Teacher.faculty,
                func.count(Teacher.user_id).label("total")
            )
            .group_by(Teacher.faculty)
        )

        # Students
        students_result = await session.execute(
            select(
                Student.faculty,
                func.count(Student.user_id).label("total")
            )
            .group_by(Student.faculty)
        )

        faculty_totals = {}

        # Teacher + Tutor qo‘shamiz
        for faculty, total in teachers_result.all():
            faculty_totals[faculty] = faculty_totals.get(faculty, 0) + total

        # Student qo‘shamiz
        for faculty, total in students_result.all():
            faculty_totals[faculty] = faculty_totals.get(faculty, 0) + total

        # Tartiblab qaytaramiz (eng kattadan)
        sorted_data = sorted(
            faculty_totals.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_data

# =============================
# 📊 UNIVERSITET UMUMIY STATISTIKASI
# =============================
async def get_university_statistics():
    async with AsyncSessionLocal() as session:

        # ===== O‘QITUVCHI / TYUTOR =====
        teachers_result = await session.execute(
            select(Teacher.role, func.count(Teacher.user_id))
            .group_by(Teacher.role)
        )
        teacher_rows = teachers_result.all()

        teacher_count = 0
        tutor_count = 0

        for role, count in teacher_rows:
            role = (role or "").lower()
            if role in ["o‘qituvchi", "teacher"]:
                teacher_count += count
            elif role in ["tyutor", "tutor"]:
                tutor_count += count

        # ===== TALABALAR =====
        students_result = await session.execute(
            select(func.count(Student.user_id))
        )
        student_count = students_result.scalar() or 0

        # ===== FAKULTETLAR BO‘YICHA (3 ta jadvaldan) =====
        faculty_stat = {}

        # Teachers
        t_fac = await session.execute(
            select(Teacher.faculty, func.count(Teacher.user_id))
            .group_by(Teacher.faculty)
        )
        for fac, count in t_fac.all():
            fac = fac or "Noma’lum"
            faculty_stat[fac] = faculty_stat.get(fac, 0) + count

        # Students
        s_fac = await session.execute(
            select(Student.faculty, func.count(Student.user_id))
            .group_by(Student.faculty)
        )
        for fac, count in s_fac.all():
            fac = fac or "Noma’lum"
            faculty_stat[fac] = faculty_stat.get(fac, 0) + count

        total_users = teacher_count + tutor_count + student_count

        return {
            "total_users": total_users,
            "teacher_count": teacher_count,
            "tutor_count": tutor_count,
            "student_count": student_count,
            "faculty_stat": faculty_stat,
        }
