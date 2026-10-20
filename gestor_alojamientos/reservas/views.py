from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import FormView

from .forms import DisponibilidadForm
from .services import LIBRE, buscar_disponibilidad


class SoloStaffMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Exige sesion iniciada Y que la cuenta sea de staff."""

    def test_func(self):
        return self.request.user.is_staff


class DisponibilidadView(SoloStaffMixin, FormView):
    """Buscador: dadas unas fechas, muestra que departamentos estan libres."""

    template_name = "reservas/disponibilidad.html"
    form_class = DisponibilidadForm

    def get_form_kwargs(self):
        # El formulario se envia por GET (los datos van en la direccion),
        # asi se puede recargar o guardar la busqueda.
        kwargs = super().get_form_kwargs()
        if self.request.GET:
            kwargs["data"] = self.request.GET
        return kwargs

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        contexto = self.get_context_data(form=form)
        if request.GET and form.is_valid():
            datos = form.cleaned_data
            resultados = buscar_disponibilidad(
                datos["fecha_ingreso"],
                datos["fecha_egreso"],
                personas=datos["personas"],
                planta_baja=datos["planta_baja"],
                deck=datos["deck"],
            )
            contexto.update(
                resultados=resultados,
                noches=(datos["fecha_egreso"] - datos["fecha_ingreso"]).days,
                libres=sum(1 for r in resultados if r["estado"] == LIBRE),
                mascota=datos["mascota"],
                buscado=True,
            )
        return self.render_to_response(contexto)
