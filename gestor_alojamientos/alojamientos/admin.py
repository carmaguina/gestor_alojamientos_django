# alojamientos/admin.py
from django.contrib import admin
from .models import Unidad

@admin.action(description="Marcar unidades seleccionadas como activas")
def marcar_como_activas(modeladmin, request, queryset):
    queryset.update(activa=True)

@admin.action(description="Marcar unidades seleccionadas como inactivas")
def marcar_como_inactivas(modeladmin, request, queryset):
    queryset.update(activa=False)

class UnidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'capacidad', 'activa', 'planta_baja', 'tiene_deck', 'color')
    search_fields = ('nombre', )
    list_filter = ('activa', 'capacidad')
    actions = [marcar_como_activas, marcar_como_inactivas]

admin.site.register(Unidad, UnidadAdmin)