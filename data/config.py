import os
from dotenv import load_dotenv

# .env ni ANIQ YO‘L bilan yuklaymiz
load_dotenv("data/.env")

def parse_ids(value: str):
    if not value:
        return []
    return [int(x) for x in value.split(",") if x.strip().isdigit()]

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMINS = parse_ids(os.getenv("ADMINS", ""))

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

# asyncpg ga majburiy o‘tkazamiz
DATABASE_URL = DATABASE_URL.replace(
    "postgresql://",
    "postgresql+asyncpg://"
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
    "Tabiiy fanlar va tibbiyot fakulteti": {
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
    "O‘zbek filologiyasi fakulteti": {
        "teacher": parse_ids(os.getenv("RAHBAR_TEACHER_UZBEK", "")),
        "student": parse_ids(os.getenv("RAHBAR_STUDENT_UZBEK", "")),
    },
    "Tibbiyot fakulteti": {
        "teacher": parse_ids(os.getenv("RAHBAR_TEACHER_MED", "")),
        "student": parse_ids(os.getenv("RAHBAR_STUDENT_MED", "")),
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

def normalize_faculty(text: str) -> str:
    if not text:
        return ""

    return (
        text.lower()
            .replace("fakulteti", "")
            .replace("fakultet", "")
            .replace("ga", "")
            .replace("dan", "")
            .replace("iga", "")
            .replace("  ", " ")
            .strip()
            .title()
    )
