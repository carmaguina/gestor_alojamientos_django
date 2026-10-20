from django import forms


class DisponibilidadForm(forms.Form):
    fecha_ingreso = forms.DateField(
        label="Ingreso", widget=forms.DateInput(attrs={"type": "date"})
    )
    fecha_egreso = forms.DateField(
        label="Egreso", widget=forms.DateInput(attrs={"type": "date"})
    )
    personas = forms.IntegerField(label="Personas", min_value=1, max_value=20, required=False)
    planta_baja = forms.BooleanField(label="Solo planta baja", required=False)
    deck = forms.BooleanField(label="Con deck privado", required=False)
    mascota = forms.BooleanField(label="Viajan con mascota", required=False)

    def clean(self):
        datos = super().clean()
        ingreso = datos.get("fecha_ingreso")
        egreso = datos.get("fecha_egreso")
        if ingreso and egreso and egreso <= ingreso:
            self.add_error("fecha_egreso", "El egreso debe ser posterior al ingreso.")
        return datos
