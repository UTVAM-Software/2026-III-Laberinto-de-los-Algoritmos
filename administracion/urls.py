from django.urls import path
from . import views as v

app_name = "administracion"
urlpatterns = [
    path("", v.Dashboard.as_view(), name="dashboard"),
    path("<slug:entity>/", v.Records.as_view(), name="list"),
    path("<slug:entity>/nuevo/", v.RecordCreate.as_view(), name="create"),
    path("<slug:entity>/<str:pk>/", v.RecordDetail.as_view(), name="detail"),
    path("<slug:entity>/<str:pk>/editar/", v.RecordForm.as_view(), name="update"),
    path("<slug:entity>/<str:pk>/eliminar/", v.RecordDelete.as_view(), name="delete"),
]
