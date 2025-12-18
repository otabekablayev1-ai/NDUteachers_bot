import os
from dotenv import load_dotenv

# .env ni yuklash
load_dotenv()

# ===============================================
# 🧩 Yordamchi FUNKSIYA (ENG MUHIMI)
# ===============================================
def parse_ids(value: str):
    """Vergul bilan ajratilgan ID-larni int listga aylantiradi."""
    if not value:
        return []
    return [int(x) for x in value.split(",") if x.strip().isdigit()]

# ===============================================
# 🔐 BOT SOZLAMALARI
# ===============================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMINS = parse_ids(os.getenv("ADMINS", ""))

DB_PATH = os.getenv(
    "DB_PATH",
    os.path.join(os.path.dirname(__file__), "..", "database", "bot.db")
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{DB_PATH}"
)

# ===============================================
# 🏫 FAKULTET MENEJERLARI (Talaba va O‘qituvchi yo‘nalishida)
# ===============================================
MANAGERS_BY_FACULTY = {
    "Aniq fanlar fakulteti": {
        "teacher": parse_ids(os.getenv("RAHBAR_TEACHER_MATH", "")),
        "student": parse_ids(os.getenv("RAHBAR_STUDENT_MATH", "")),
    },
    "Iqtisodiyot fakulteti": {
        "teacher": parse_ids(os.getenv("RAHBAR_TEACHER_ECON", "")),
        "student": parse_ids(os.getenv("RAHBAR_STUDENT_ECON", "")),
    },
    "Maktabgacha va boshlang‘ich ta’lim fakulteti": {
        "teacher": parse_ids(os.getenv("RAHBAR_TEACHER_PRE", "")),
        "student": parse_ids(os.getenv("RAHBAR_STUDENT_PRE", "")),
    },
    "San’at va sport fakulteti": {
        "teacher": parse_ids(os.getenv("RAHBAR_TEACHER_SPORT", "")),
        "student": parse_ids(os.getenv("RAHBAR_STUDENT_SPORT", "")),
    },
    "Tabiiy va tibbiyot fakulteti": {
        "teacher": parse_ids(os.getenv("RAHBAR_TEACHER_BIO", "")),
        "student": parse_ids(os.getenv("RAHBAR_STUDENT_BIO", "")),
    },
    "Tarix fakulteti": {
        "teacher": parse_ids(os.getenv("RAHBAR_TEACHER_HIST", "")),
        "student": parse_ids(os.getenv("RAHBAR_STUDENT_HIST", "")),
    },
    "Tillar fakulteti": {
        "teacher": parse_ids(os.getenv("RAHBAR_TEACHER_LANG", "")),
        "student": parse_ids(os.getenv("RAHBAR_STUDENT_LANG", "")),
    },
}

def is_manager_id(user_id: int) -> bool:
    """
    user_id MANAGERS_BY_FACULTY ichida bormi?
    """
    for fac in MANAGERS_BY_FACULTY.values():
        if user_id in fac.get("student", []) or user_id in fac.get("teacher", []):
            return True
    return False


# ===============================================
# 🧑‍💼 UMUMIY RAHBARLAR (barcha rollar uchun)
# ===============================================
RAHBARLAR = {
    "Prorektor (O‘quv ishlari bo‘yicha)": parse_ids(os.getenv("RAHBAR_PROREKTOR", "")),
    "Prorektor (Yoshlar masalalari va MMIB)": parse_ids(os.getenv("RAHBAR_PROREKTOR_YOSHLAR", "")),
    "O'quv-uslubiy boshqarma (Departament)": parse_ids(os.getenv("RAHBAR_DEPARTAMENT", "")),
    "Registrator ofisi direktori": parse_ids(os.getenv("RAHBAR_REGISTRATOR", "")),
    "Ariza va shikoyatlar": parse_ids(os.getenv("RAHBAR_ANTI", "")),
    "Magistratura bo‘limi": parse_ids(os.getenv("RAHBAR_MAG_BOSH", "")),
    "Buxgalteriya (Ustozlar)": parse_ids(os.getenv("RAHBAR_BUX_TEACHER", "")),
    "Buxgalteriya (Talabalar)": parse_ids(os.getenv("RAHBAR_BUX_DORMIT_STUDENT", "")),
    "Xalqaro aloqalar va akademik mobillik boʻyicha xizmat koʻrsatish sektori menejeri": parse_ids(os.getenv("RAHBAR_XALQARO", "")),
}

# Izoh:
# - MANAGERS_BY_FACULTY — fakultet mas'ullari (math, econ, lang... bo‘yicha)
# - RAHBARLAR — umumiy prorektor, registrator va hokazo


# ===============================================
# 🧩 Foydali yordamchi funksiya
# ===============================================
def parse_ids(value: str):
    """Vergul bilan ajratilgan ID-larni int listga aylantiradi."""
    return [int(x) for x in value.split(",") if x.strip().isdigit()]

def normalize_faculty(name: str) -> str:
    if not name:
        return ""
    return (
        name.replace("ga", "")
            .replace("dan", "")
            .replace("iga", "")
            .replace("iga", "")
            .replace("  ", " ")
            .strip()
    )

