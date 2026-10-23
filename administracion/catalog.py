"""Catálogo explícito de entidades administrables. No acepta modelos por URL."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from escuela.models import Classroom, Student
from preguntas.models import Subject, Category, Question
from juego.models import Attempt, AttemptQuestion
from progreso.models import Mastery, WorldUnlock

CATALOG = {
    "usuarios": (get_user_model(), "Usuarios", ("username", "first_name", "last_name", "email")),
    "roles": (Group, "Roles y grupos de permisos", ("name",)),
    "permisos": (Permission, "Permisos", ("name", "codename")),
    "materias": (Subject, "Materias", ("name",)),
    "categorias": (Category, "Categorías", ("name", "code")),
    "grupos": (Classroom, "Grupos escolares", ("name",)),
    "alumnos": (Student, "Alumnos", ("name", "user__username")),
    "preguntas": (Question, "Preguntas", ("text", "topic")),
    "partidas": (Attempt, "Partidas", ("student__name",)),
    "respuestas": (AttemptQuestion, "Preguntas de partida", ("attempt__student__name",)),
    "aprendizajes": (Mastery, "Aprendizajes logrados", ("student__name", "question__text")),
    "desbloqueos": (WorldUnlock, "Mundos desbloqueados", ("student__name", "category__name")),
}

FIELDS = {
    "roles": ("name", "permissions"),
    "permisos": ("name", "content_type", "codename"),
    "materias": ("name",),
    "categorias": ("code", "name", "min_age", "max_age", "seconds", "routes"),
    "grupos": ("name", "teacher", "active"),
    "alumnos": ("name", "user", "teacher", "classrooms", "category", "difficulty", "age", "active"),
    "preguntas": ("subject", "category", "difficulty", "topic", "text", "option_a", "option_b", "option_c", "option_d", "correct", "explanation", "status", "author"),
    "partidas": ("student", "operator", "category", "difficulty", "seconds", "mode", "state", "board", "total_questions", "current", "deadline", "next_at", "score", "finished_at"),
    "respuestas": ("attempt", "question", "position", "snapshot", "selected", "correct", "answered_at"),
    "aprendizajes": ("student", "question", "category"),
    "desbloqueos": ("student", "category"),
}
