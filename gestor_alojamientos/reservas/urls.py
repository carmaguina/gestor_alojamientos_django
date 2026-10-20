from django.urls import path

from . import views

app_name = "reservas"

urlpatterns = [
    path("disponibilidad/", views.DisponibilidadView.as_view(), name="disponibilidad"),
]
