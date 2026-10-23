"""CRUD administrativo con autenticación, permiso por acción y CSRF."""
from django.contrib import messages
from django.contrib.auth import get_user_model, update_session_auth_hash
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.admin.utils import NestedObjects
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.db.models.deletion import ProtectedError, RestrictedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import TemplateView, ListView, DetailView, FormView
from .catalog import CATALOG
from .forms import form_for


class AdminAccess(LoginRequiredMixin, PermissionRequiredMixin):
    action = "view"
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_active or not request.user.is_superuser:
            raise PermissionDenied
        self.key = kwargs.get("entity")
        if self.key:
            if self.key not in CATALOG:
                raise Http404
            self.model, self.title, self.search_fields = CATALOG[self.key]
        return super().dispatch(request, *args, **kwargs)

    def get_permission_required(self):
        if not self.key:
            return ("auth.view_permission",)
        meta = self.model._meta
        return (f"{meta.app_label}.{self.action}_{meta.model_name}",)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.key:
            context.update(entity=self.key, title=self.title, list_url=reverse("administracion:list", args=[self.key]))
        return context

    def record(self):
        try:
            return get_object_or_404(self.model, pk=self.kwargs["pk"])
        except (ValidationError, ValueError, TypeError):
            raise Http404


class Dashboard(AdminAccess, TemplateView):
    template_name = "administracion/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sections"] = [{"key": key, "title": label, "count": model.objects.count()} for key, (model, label, _) in CATALOG.items()]
        return context


class Records(AdminAccess, ListView):
    template_name = "administracion/list.html"
    paginate_by = 25

    def get_queryset(self):
        qs = self.model.objects.all().order_by("pk")
        query = self.request.GET.get("q", "").strip()
        if query:
            condition = Q()
            for field in self.search_fields:
                condition |= Q(**{f"{field}__icontains": query})
            qs = qs.filter(condition).distinct()
        return qs


class RecordDetail(AdminAccess, DetailView):
    template_name = "administracion/detail.html"

    def get_object(self, queryset=None):
        return self.record()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rows = []
        for field in self.model._meta.fields:
            if field.name in {"password", "display_token", "claim_code", "invite_code"}:
                continue
            value = getattr(self.object, field.name)
            display = getattr(self.object, f"get_{field.name}_display", None)
            rows.append((field.verbose_name, display() if display else value))
        for field in self.model._meta.many_to_many:
            rows.append((field.verbose_name, ", ".join(str(value) for value in getattr(self.object, field.name).all()) or "—"))
        context["rows"] = rows
        return context


class RecordForm(AdminAccess, FormView):
    template_name = "administracion/form.html"
    creating = False
    action = "change"

    def get_form_class(self):
        return form_for(self.key, self.creating)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if not self.creating:
            kwargs["instance"] = self.record()
        return kwargs

    def form_valid(self, form):
        if self.key == "usuarios" and not self.creating and form.instance.pk == self.request.user.pk:
            if not form.cleaned_data.get("is_active") or not form.cleaned_data.get("is_superuser"):
                form.add_error(None, "No puedes desactivar tu propia cuenta ni quitarte el rol de administrador.")
                return self.form_invalid(form)
        try:
            with transaction.atomic():
                obj = form.save()
        except (IntegrityError, ValidationError):
            form.add_error(None, "No se pudo guardar: revisa los valores únicos y las relaciones.")
            return self.form_invalid(form)
        if self.key == "usuarios" and obj.pk == self.request.user.pk:
            update_session_auth_hash(self.request, obj)
        messages.success(self.request, "Registro guardado correctamente.")
        return redirect("administracion:detail", entity=self.key, pk=obj.pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["creating"] = self.creating
        return context


class RecordCreate(RecordForm):
    action = "add"
    creating = True


class RecordDelete(AdminAccess, TemplateView):
    action = "delete"
    template_name = "administracion/delete.html"

    def deletion_info(self, obj):
        collector = NestedObjects(using=obj._state.db)
        collector.collect([obj])
        affected = [(model._meta.verbose_name_plural, len(objects)) for model, objects in collector.data.items()]
        return affected, bool(collector.protected)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.record()
        affected, protected = self.deletion_info(obj)
        context.update(object=obj, affected=affected, protected=protected)
        return context

    def post(self, request, *args, **kwargs):
        obj = self.record()
        url = reverse("administracion:list", args=[self.key])
        if self.key == "usuarios":
            last_admin = obj.is_superuser and obj.is_active and not get_user_model().objects.filter(is_superuser=True, is_active=True).exclude(pk=obj.pk).exists()
            if obj.pk == request.user.pk or last_admin:
                messages.error(request, "No puedes eliminar tu propia cuenta ni al último administrador activo.")
                return redirect(url)
        try:
            with transaction.atomic():
                obj.delete()
        except (ProtectedError, RestrictedError, IntegrityError):
            messages.error(request, "No se puede eliminar: otros registros dependen de este elemento. Conserva el historial o modifica primero sus relaciones.")
            return redirect(url)
        messages.success(request, "Registro eliminado.")
        return redirect(url)
