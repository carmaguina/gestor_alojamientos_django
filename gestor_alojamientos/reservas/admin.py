from django.contrib import admin

from .models import Cierre, Huesped, Reserva


@admin.action(description="Marcar reservas seleccionadas como señadas")
def marcar_como_seniadas(modeladmin, request, queryset):
    queryset.update(estado=Reserva.ESTADO_SENIADA)


@admin.action(description="Marcar reservas seleccionadas como canceladas")
def marcar_como_canceladas(modeladmin, request, queryset):
    queryset.update(estado=Reserva.ESTADO_CANCELADA)


@admin.register(Huesped)
class HuespedAdmin(admin.ModelAdmin):
    list_display = ("nombre", "apellido", "email", "telefono", "fecha_creacion")
    search_fields = ("nombre", "apellido", "email", "telefono")
    list_filter = ("fecha_creacion",)


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = (
        "huesped",
        "unidad",
        "fecha_ingreso",
        "fecha_egreso",
        "cantidad_personas",
        "estado",
        "monto_senia",
    )
    search_fields = (
        "huesped__nombre",
        "huesped__apellido",
        "huesped__email",
        "unidad__nombre",
    )
    list_filter = ("estado", "unidad", "fecha_ingreso", "lleva_mascota")
    actions = [marcar_como_seniadas, marcar_como_canceladas]


@admin.register(Cierre)
class CierreAdmin(admin.ModelAdmin):
    list_display = ("unidad", "fecha_desde", "fecha_hasta", "motivo")
    list_filter = ("unidad",)
