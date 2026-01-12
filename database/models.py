
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Text,
    DateTime,
    Boolean,
    ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from sqlalchemy.orm import relationship
Base = declarative_base()

# =========================
# 👤 O‘QITUVCHI / TYUTOR
# =========================
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20))
    # student | teacher | tutor | manager

class Teacher(Base):
    __tablename__ = "teachers"

    user_id = Column(BigInteger, primary_key=True)  # ✅ ASOSIY KALIT
    fio = Column(String)
    phone = Column(String)
    faculty = Column(String)
    role = Column(String)

class Student(Base):
    __tablename__ = "students"
    user_id = Column(BigInteger, primary_key=True)
    fio = Column(String)
    phone = Column(String)
    faculty = Column(String)
    edu_type = Column(String)
    edu_form = Column(String)
    course = Column(String)
    student_group = Column(String)
    passport = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# =========================
# 📩 RO‘YXATDAN O‘TISH SO‘ROVI
# =========================
class RegisterRequest(Base):
    __tablename__ = "register_requests"

    user_id = Column(BigInteger, primary_key=True)   # Telegram ID
    fio = Column(String)
    phone = Column(String)
    faculty = Column(String)
    department = Column(String)
    passport = Column(String)
    role = Column(String)       # O‘qituvchi / Tyutor / Talaba
    edu_type = Column(String)
    edu_form = Column(String)
    course = Column(String)
    student_group = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# =========================
# ❓ SAVOLLAR
# =========================
class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    sender_id = Column(BigInteger, nullable=False)
    sender_role = Column(String, nullable=False)     # <-- NOT NULL
    fio = Column(String)
    faculty = Column(String)
    message_text = Column(Text)
    answered = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    answers = relationship(
        "Answer",
        back_populates="question",
        cascade="all, delete-orphan"
    )
# =========================
# 🧾 JAVOBLAR
# =========================
from sqlalchemy import Column, Integer, BigInteger, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

class Answer(Base):
    __tablename__ = "answers"
    id = Column(Integer, primary_key=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    manager_id = Column(BigInteger, nullable=False)
    answer_text = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    question = relationship("Question", back_populates="answers")# =========================
# ⭐ REYTING
# =========================
class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(BigInteger)
    manager_id = Column(BigInteger)
    question_id = Column(Integer)
    rating = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

# =========================
# ⭐ MENEJER REYTINGI (ixtiyoriy)
# =========================
class ManagerRating(Base):
    __tablename__ = "manager_ratings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger)
    manager_id = Column(BigInteger)
    question_id = Column(Integer)
    rating = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

# =========================
# 📘 BUYRUQLAR
# =========================
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String)
    file_id = Column(String)
    uploaded_by = Column(BigInteger)
    created_at = Column(DateTime, default=datetime.utcnow)

# =========================
# 🔗 BUYRUQ LINKLARI
# =========================
class OrderLink(Base):
    __tablename__ = "orders_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, nullable=False)
    link = Column(String, nullable=False)
    year = Column(String)
    faculty = Column(String)
    type = Column(String)
    students = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

# =========================
# 👔 MENEJER ISMI
# =========================
class Manager(Base):
    __tablename__ = "managers"

    user_id = Column(BigInteger, primary_key=True)
    full_name = Column(String)

# =========================
# 📎 BUYRUQLAR FAYLI
# =========================
class CommandsFile(Base):
    __tablename__ = "commands_file"

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
