from django.contrib import messages
from django.core.exceptions import ValidationError
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
    FormView,
)
from escuela.models import Student
from escuela.models import Classroom
from escuela.forms import (
    ClassroomForm,
    StudentCreateForm,
    StudentForm,
    JoinGroupForm,
    GroupChoiceForm,
    PupilFormSet,
    ClaimProfileForm,
)
from core.access import is_manager, students_for, classrooms_for
from progreso.services.progress import category_for_age

from django.views import View
from core.mixins import SchoolPermission, OperatorFormMixin, ScopedQuerysetMixin


class ClassroomList(SchoolPermission, ListView):
    permission_required = "escuela.view_classroom"
    template_name = "escuela/classrooms.html"

    def get_queryset(self):
        return classrooms_for(self.request.user).annotate(total=Count("student"))


class ClassroomDetail(ScopedQuerysetMixin, SchoolPermission, DetailView):
    permission_required = "escuela.view_classroom"
    template_name = "escuela/classroom_detail.html"
    scope = staticmethod(classrooms_for)

    def get_context_data(self, **kwargs):
        c = super().get_context_data(**kwargs)
        c["students"] = students_for(self.request.user).filter(classrooms=self.object)
        return c


class ClassroomCreate(SchoolPermission, CreateView):
    permission_required = "escuela.add_classroom"
    model = Classroom
    form_class = ClassroomForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("escuela:classrooms")
    extra_context = {"title": "Crear grupo"}

    def form_valid(self, form):
        form.instance.teacher = self.request.user
        return super().form_valid(form)


class ClassroomUpdate(ScopedQuerysetMixin, SchoolPermission, UpdateView):
    permission_required = "escuela.change_classroom"
    form_class = ClassroomForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("escuela:classrooms")
    extra_context = {"title": "Editar grupo"}
    scope = staticmethod(classrooms_for)


class ClassroomDelete(ScopedQuerysetMixin, SchoolPermission, DeleteView):
    permission_required = "escuela.delete_classroom"
    template_name = "shared/delete.html"
    success_url = reverse_lazy("escuela:classrooms")
    scope = staticmethod(classrooms_for)

    def form_valid(self, form):
        if self.object.student_set.exists():
            self.object.active = False
            self.object.save()
            messages.info(self.request, "Grupo archivado. Se conservan sus alumnos.")
            return redirect(self.success_url)
        return super().form_valid(form)


class StudentList(SchoolPermission, ListView):
    permission_required = "escuela.view_student"
    template_name = "escuela/students.html"

    def get_queryset(self):
        qs = students_for(self.request.user)

        category = self.request.GET.get("category")
        if category:
            qs = qs.filter(category__code=category)

        search = self.request.GET.get("q", "").strip()
        if search:
            qs = qs.filter(name__icontains=search)

        return qs


class StudentDetail(ScopedQuerysetMixin, SchoolPermission, DetailView):
    permission_required = "escuela.view_student"
    template_name = "escuela/student_detail.html"
    scope = staticmethod(students_for)

    def get_context_data(self, **kwargs):
        c = super().get_context_data(**kwargs)
        c["attempts"] = self.object.attempts.all()[:30]
        return c


class StudentCreate(OperatorFormMixin, SchoolPermission, FormView):
    permission_required = "escuela.add_student"
    form_class = StudentCreateForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("escuela:students")
    extra_context = {
        "title": "Añadir participante",
        "hint": "Solo nombre, edad y grupo. Se guardará su progreso sin crearle una contraseña.",
    }

    def form_valid(self, form):
        form.save()
        return redirect(self.success_url)


class StudentUpdate(
    OperatorFormMixin, ScopedQuerysetMixin, SchoolPermission, UpdateView
):
    permission_required = "escuela.change_student"
    form_class = StudentForm
    template_name = "shared/form.html"
    success_url = reverse_lazy("escuela:students")
    extra_context = {"title": "Editar alumno"}
    scope = staticmethod(students_for)


class StudentDelete(ScopedQuerysetMixin, SchoolPermission, DeleteView):
    permission_required = "escuela.delete_student"
    template_name = "shared/delete.html"
    success_url = reverse_lazy("escuela:students")
    scope = staticmethod(students_for)

    @transaction.atomic
    def form_valid(self, form):
        if self.object.self_registered and not self.request.user.is_superuser:
            self.object.classrooms.clear()
            self.object.teacher = None
            self.object.save(update_fields=["teacher"])
            messages.info(
                self.request,
                "Alumno desvinculado. Su cuenta y su progreso personal se conservan.",
            )
        elif self.object.attempts.exists():
            self.object.active = False
            self.object.save()
            if self.object.user_id:
                self.object.user.is_active = False
                self.object.user.save()
            messages.info(
                self.request, "Alumno desactivado; su historial está protegido."
            )
        else:
            user = self.object.user
            self.object.delete()
            if user:
                user.delete()
        return redirect(self.success_url)


class StudentConnectionView(LoginRequiredMixin, FormView):
    template_name = "shared/form.html"
    success_url = reverse_lazy("cuentas:profile")

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            if is_manager(request.user):
                return HttpResponseForbidden("Esta opción es para alumnos.")
            self.student = get_object_or_404(Student, user=request.user, active=True)
        return super().dispatch(request, *args, **kwargs)


class JoinGroupView(StudentConnectionView):
    form_class = JoinGroupForm
    extra_context = {
        "title": "Unirme a un grupo",
        "submit_label": "Unirme al grupo",
        "hint": "Es opcional. Al unirte, tu profesor podrá consultar tu progreso y ajustar tu nivel.",
    }

    def form_valid(self, form):
        from escuela.services.accounts import join_group

        try:
            room = join_group(self.student.pk, form.cleaned_data["group_code"])
        except ValidationError as error:
            form.add_error("group_code", error)
            return self.form_invalid(form)
        messages.success(self.request, f"Ya formas parte de {room.name}.")
        return super().form_valid(form)


class RotateInvitationView(SchoolPermission, View):
    permission_required = "escuela.change_classroom"

    def post(self, request, pk):
        from core.codes import invitation_code

        room = get_object_or_404(classrooms_for(request.user), pk=pk)
        room.invite_code = invitation_code()
        room.save(update_fields=["invite_code"])
        messages.success(
            request,
            "Código cambiado. El anterior ya no admite alumnos; las inscripciones existentes se conservan.",
        )
        return redirect("escuela:classroom_detail", pk=pk)


class BulkStudentsView(SchoolPermission, View):
    permission_required = "escuela.add_student"

    def get(self, request, *args, **kwargs):
        return self.handle_form(request)

    def post(self, request, *args, **kwargs):
        return self.handle_form(request)

    def handle_form(self, request):
        group_form = GroupChoiceForm(request.POST or None, operator=request.user)
        formset = PupilFormSet(request.POST or None, prefix="pupils")
        if request.method == "POST":
            valid_group = group_form.is_valid()
            valid_rows = formset.is_valid()
            if valid_group and valid_rows:
                import uuid

                with transaction.atomic():
                    group = group_form.group()
                    count = 0
                    for form in formset:
                        if not form.cleaned_data:
                            continue
                        data = form.cleaned_data
                        pupil = Student.objects.create(
                            name=data["name"],
                            age=data["age"],
                            category=category_for_age(data["age"]),
                            teacher=request.user,
                            claim_code=uuid.uuid4().hex,
                        )
                        if group:
                            pupil.classrooms.add(group)
                        count += 1
                messages.success(request, f"{count} participantes añadidos.")
                return redirect("escuela:students")
        return render(
            request,
            "escuela/bulk_students.html",
            {"group_form": group_form, "formset": formset},
        )


class ClaimProfileView(StudentConnectionView):
    form_class = ClaimProfileForm
    extra_context = {
        "title": "Vincular mi perfil de clase",
        "submit_label": "Vincular mi perfil",
        "hint": "Usa solo el código personal que tu profesor te entregó para tu propio perfil. Se combinarán los historiales.",
    }

    def form_valid(self, form):
        from escuela.services.accounts import claim_profile

        try:
            student = claim_profile(self.request.user, form.cleaned_data["code"])
        except ValidationError as error:
            form.add_error("code", error)
            return self.form_invalid(form)
        messages.success(
            self.request,
            f"Tu cuenta ya está vinculada a {student}. Se conservó el progreso.",
        )
        return super().form_valid(form)
