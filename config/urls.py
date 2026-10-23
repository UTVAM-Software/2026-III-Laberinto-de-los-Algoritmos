from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("gestion/", include("administracion.urls")),
    path("admin/", admin.site.urls),
    path("", include("cuentas.urls")),
    path("", include("inicio.urls")),
    path("", include("escuela.urls")),
    path("", include("preguntas.urls")),
    path("", include("juego.urls")),
    path("", include("progreso.urls")),
]
