from . import student_orders
from . import admin_delete_order
from . import (
    start,
    registration,
    admin,
    admin_message,
    admin_register_check,
    teacher_panel,
    student_panel,
    heads,
    commands_orders,   # YANGI MODUL
)

__all__ = [
    "start",
    "registration",
    "teacher_panel",
    "student_panel",
    "admin",
    "admin_message",
    "admin_register_check",
    "heads",
    "commands_orders",
    "student_orders",
    "admin_delete_order.py"
]
