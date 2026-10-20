from django.db import models

class Unidad(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    capacidad = models.PositiveIntegerField()
    activa = models.BooleanField(default=True)

    # --- NUEVO: caracteristicas para el buscador de disponibilidad ---
    planta_baja = models.BooleanField(
        "Planta baja", default=False,
        help_text="Sin escaleras. Útil para huéspedes con dificultad para subir.",
    )
    tiene_deck = models.BooleanField("Tiene deck privado", default=False)
    # Color con el que se dibuja este departamento en el calendario (formato #RRGGBB)
    color = models.CharField(
        "Color en el calendario", max_length=7, default="#B23A2A",
        help_text="Formato #RRGGBB, por ejemplo #8DB600.",
    )

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Unidad"
        verbose_name_plural = "Unidades"