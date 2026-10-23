from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management import call_command
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from escuela.models import Student, Classroom
from preguntas.models import Category, Subject, Question
from juego.models import Attempt, AttemptQuestion
from progreso.models import Mastery, WorldUnlock
from .catalog import CATALOG


@override_settings(SECURE_SSL_REDIRECT=False, STORAGES={"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}, "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"}})
class AdministrationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_initial", verbosity=0)
        User = get_user_model()
        cls.admin = User.objects.create_superuser("crud_admin", "admin@example.test", "UnicaSegura_9274")
        cls.teacher = User.objects.create_user("crud_teacher")
        cls.teacher.groups.add(Group.objects.get(name="Profesor"))
        cls.child = User.objects.create_user("crud_child")
        cls.child.groups.add(Group.objects.get(name="Alumno"))
        cls.category = Category.objects.get(code="ALFA")
        cls.student = Student.objects.create(name="Ana", age=7, category=cls.category, teacher=cls.teacher, user=cls.child)
        cls.room = Classroom.objects.create(name="Grupo", teacher=cls.teacher)
        cls.question = Question.objects.first()
        cls.attempt = Attempt.objects.create(student=cls.student, operator=cls.teacher, category=cls.category, difficulty=1, seconds=0, mode="solo")
        cls.item = AttemptQuestion.objects.create(attempt=cls.attempt, question=cls.question, position=0, snapshot={})
        cls.mastery = Mastery.objects.create(student=cls.student, question=cls.question, category=cls.category)
        cls.unlock = WorldUnlock.objects.create(student=cls.student, category=cls.category)

    def url(self, action, key, pk=None):
        args = [key] if pk is None else [key, pk]
        return reverse("administracion:" + action, args=args)

    def test_admin_can_render_all_lists_details_create_update_and_delete_forms(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse("administracion:dashboard")).status_code, 200)
        for key, (model, _, _) in CATALOG.items():
            obj = model.objects.first()
            for action in ("list", "create", "detail", "update", "delete"):
                with self.subTest(entity=key, action=action):
                    url = self.url(action, key, obj.pk if action in ("detail", "update", "delete") else None)
                    self.assertEqual(self.client.get(url).status_code, 200)

    def test_anonymous_teacher_and_student_cannot_access_or_mutate_admin_crud(self):
        for user in (None, self.teacher, self.child):
            self.client.logout()
            if user:
                self.client.force_login(user)
            for key, (model, _, _) in CATALOG.items():
                obj = model.objects.first()
                for action in ("list", "create", "detail", "update", "delete"):
                    url = self.url(action, key, obj.pk if action in ("detail", "update", "delete") else None)
                    with self.subTest(user=user, entity=key, action=action):
                        self.assertEqual(self.client.get(url).status_code, 403)
                        self.assertEqual(self.client.post(url, {"is_superuser": "on"}).status_code, 403)

    def test_user_crud_hashes_passwords_and_assigns_groups_and_direct_permissions(self):
        self.client.force_login(self.admin)
        group = Group.objects.get(name="Profesor")
        perm = Permission.objects.get(codename="view_student", content_type__app_label="escuela")
        data = dict(username="new_account", email="new@example.test", is_active="on", groups=[group.pk], user_permissions=[perm.pk], password1="UnicaSegura_9274", password2="UnicaSegura_9274")
        response = self.client.post(self.url("create", "usuarios"), data)
        self.assertEqual(response.status_code, 302)
        user = get_user_model().objects.get(username="new_account")
        self.assertTrue(user.check_password(data["password1"]))
        self.assertTrue(user.groups.filter(pk=group.pk).exists())
        self.assertTrue(user.user_permissions.filter(pk=perm.pk).exists())
        data.update(username="changed_account", password1="", password2="")
        self.assertEqual(self.client.post(self.url("update", "usuarios", user.pk), data).status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.check_password("UnicaSegura_9274"))
        self.assertEqual(user.username, "changed_account")
        self.assertEqual(self.client.post(self.url("delete", "usuarios", user.pk)).status_code, 302)
        self.assertFalse(get_user_model().objects.filter(pk=user.pk).exists())

    def test_create_update_delete_for_each_other_entity(self):
        self.client.force_login(self.admin)
        content_type = ContentType.objects.get_for_model(Student)
        question_data = dict(subject=self.question.subject_id, category=self.category.pk, difficulty=1, topic="Prueba", text="¿Cuánto es 1 + 1?", option_a="2", option_b="3", option_c="4", option_d="5", correct=0, explanation="Uno más uno es dos.", status="draft", author=self.teacher.pk)
        cases = {
            "roles": dict(name="Rol de prueba", permissions=[Permission.objects.first().pk]),
            "permisos": dict(name="Prueba de permiso", content_type=content_type.pk, codename="prueba_crud"),
            "materias": dict(name="Materia de prueba"),
            "categorias": dict(code="BETA", name="Categoría de prueba", min_age=9, max_age=11, seconds=35, routes=2),
            "grupos": dict(name="Grupo de prueba", teacher=self.teacher.pk, active="on"),
            "alumnos": dict(name="Alumno de prueba", teacher=self.teacher.pk, category=self.category.pk, difficulty=1, age=8, active="on"),
            "preguntas": question_data,
            "partidas": dict(student=self.student.pk, operator=self.teacher.pk, category=self.category.pk, difficulty=1, seconds=0, mode="solo", state="ready", board='{"routes": []}', total_questions=5, current=0, score=0),
            "respuestas": dict(attempt=self.attempt.pk, question=self.question.pk, position=6, snapshot='{"text": "Prueba"}', selected=0),
            "aprendizajes": dict(student=self.student.pk, question=Question.objects.last().pk, category=self.category.pk),
            "desbloqueos": dict(student=self.student.pk, category=Category.objects.get(code="OMEGA").pk),
        }
        # Libera un código de catálogo sin tocar la categoría usada por los fixtures.
        Question.objects.filter(category__code="BETA").delete()
        Category.objects.filter(code="BETA").delete()
        for key, data in cases.items():
            model = CATALOG[key][0]
            with self.subTest(entity=key):
                before = set(model.objects.values_list("pk", flat=True))
                response = self.client.post(self.url("create", key), data)
                self.assertEqual(response.status_code, 302, response.context["form"].errors if response.status_code == 200 else "")
                pk = (set(model.objects.values_list("pk", flat=True)) - before).pop()
                response = self.client.post(self.url("update", key, pk), data)
                self.assertEqual(response.status_code, 302)
                self.assertEqual(self.client.post(self.url("delete", key, pk)).status_code, 302)
                self.assertFalse(model.objects.filter(pk=pk).exists())

    def test_get_never_deletes_and_csrf_is_required(self):
        self.client.force_login(self.admin)
        self.client.get(self.url("delete", "materias", self.question.subject_id))
        self.assertTrue(Subject.objects.filter(pk=self.question.subject_id).exists())
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.admin)
        self.assertEqual(client.post(self.url("create", "materias"), {"name": "Sin token"}).status_code, 403)

    def test_protected_delete_preserves_history_and_self_delete_is_blocked(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url("delete", "alumnos", self.student.pk))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Student.objects.filter(pk=self.student.pk).exists())
        self.client.post(self.url("delete", "usuarios", self.admin.pk))
        self.assertTrue(get_user_model().objects.filter(pk=self.admin.pk).exists())
        response = self.client.post(self.url("update", "usuarios", self.admin.pk), {"username": self.admin.username})
        self.assertEqual(response.status_code, 200)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_superuser and self.admin.is_active)

    def test_search_remains_scoped_to_each_teacher(self):
        other = get_user_model().objects.create_user("other_teacher")
        other.groups.add(Group.objects.get(name="Profesor"))
        Student.objects.create(name="Ana ajena", teacher=other, category=self.category, age=7)
        self.client.force_login(self.teacher)
        response = self.client.get(reverse("escuela:students"), {"q": " ana ", "category": "ALFA"})
        self.assertContains(response, "Ana")
        self.assertNotContains(response, "Ana ajena")
        self.assertEqual(list(response.context["object_list"]), [self.student])

    def test_unknown_entities_and_malformed_identifiers_return_404(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get('/gestion/no-existe/').status_code, 404)
        self.assertEqual(self.client.get(self.url('detail', 'partidas', 'no-es-uuid')).status_code, 404)
        self.assertEqual(self.client.get(self.url('detail', 'usuarios', 'no-es-numero')).status_code, 404)

    def test_password_validation_and_duplicate_permission_are_reported_in_form(self):
        self.client.force_login(self.admin)
        response = self.client.post(self.url('create', 'usuarios'), dict(username='weak_account', password1='123', password2='123', is_active='on'))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(username='weak_account').exists())
        permission = Permission.objects.first()
        response = self.client.post(self.url('create', 'permisos'), dict(name='Duplicado', content_type=permission.content_type_id, codename=permission.codename))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['form'].errors)
