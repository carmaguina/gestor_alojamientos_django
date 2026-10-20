from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from .models import Unidad


class UnidadListView(ListView):
    model = Unidad
    template_name = "alojamientos/unidad_list.html"
    context_object_name = "unidades"

    def get_queryset(self):
        queryset = super().get_queryset()
        query = self.request.GET.get("q", "")

        if query:
            queryset = queryset.filter(nombre__icontains=query)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        return context


class UnidadDetailView(DetailView):
    model = Unidad
    template_name = "alojamientos/unidad_detail.html"
    context_object_name = "unidad"


class UnidadCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    permission_required = "alojamientos.add_unidad"
    model = Unidad
    fields = ["nombre", "descripcion", "capacidad", "activa", "planta_baja", "tiene_deck", "color"]
    template_name = "alojamientos/unidad_form.html"
    success_url = reverse_lazy("alojamientos:unidad_list")


class UnidadUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    permission_required = "alojamientos.change_unidad"
    model = Unidad
    fields = ["nombre", "descripcion", "capacidad", "activa", "planta_baja", "tiene_deck", "color"]
    template_name = "alojamientos/unidad_form.html"
    success_url = reverse_lazy("alojamientos:unidad_list")


class UnidadDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    permission_required = "alojamientos.delete_unidad"
    model = Unidad
    template_name = "alojamientos/unidad_confirm_delete.html"
    success_url = reverse_lazy("alojamientos:unidad_list")
