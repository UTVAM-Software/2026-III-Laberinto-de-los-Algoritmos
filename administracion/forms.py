from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .catalog import CATALOG, FIELDS

User = get_user_model()
ACCOUNT_FIELDS = ("username", "first_name", "last_name", "email", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")


class AccountCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ACCOUNT_FIELDS


class AccountUpdateForm(forms.ModelForm):
    password1 = forms.CharField(label="Nueva contraseña", required=False, widget=forms.PasswordInput, help_text="Deja ambos campos vacíos para conservar la contraseña actual.")
    password2 = forms.CharField(label="Confirmar nueva contraseña", required=False, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ACCOUNT_FIELDS

    def clean(self):
        data = super().clean()
        first, second = data.get("password1"), data.get("password2")
        if first != second:
            self.add_error("password2", "Las contraseñas no coinciden.")
        if first:
            candidate = User(username=data.get("username", ""), first_name=data.get("first_name", ""), last_name=data.get("last_name", ""), email=data.get("email", ""))
            try:
                password_validation.validate_password(first, candidate)
            except ValidationError as error:
                self.add_error("password1", error)
        if self.instance.is_superuser and self.instance.is_active:
            demoting = not data.get("is_superuser") or not data.get("is_active")
            if demoting and not User.objects.filter(is_superuser=True, is_active=True).exclude(pk=self.instance.pk).exists():
                raise ValidationError("Debe permanecer al menos un administrador activo.")
        return data

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data.get("password1"):
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            self.save_m2m()
        return user


def form_for(key, creating=False):
    if key == "usuarios":
        return AccountCreateForm if creating else AccountUpdateForm
    return forms.modelform_factory(CATALOG[key][0], fields=FIELDS[key])
