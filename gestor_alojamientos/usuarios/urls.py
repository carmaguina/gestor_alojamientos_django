from django.urls import path

from .views import PerfilUpdateView, RegistroUsuarioView

app_name = 'usuarios'

urlpatterns = [
    path('perfil/', PerfilUpdateView.as_view(), name='perfil'),
]