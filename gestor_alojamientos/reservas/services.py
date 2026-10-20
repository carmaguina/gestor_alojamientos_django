"""Logica de disponibilidad, separada de las pantallas para poder probarla sola."""
from django.db.models import Q

from alojamientos.models import Unidad

from .models import Cierre, Reserva

# Estados posibles del resultado para cada departamento
LIBRE = "libre"
OCUPADO = "ocupado"
CERRADO = "cerrado"
DESCARTADO = "descartado"   # no cumple un filtro (planta baja / deck)


def reservas_que_chocan(unidad_id, ingreso, egreso, excluir_pk=None):
    """Reservas (no canceladas) de un departamento que se pisan con [ingreso, egreso).

    Se pisan si la otra empieza ANTES de que esta termine y termina DESPUES
    de que esta empiece. Los signos < y > son estrictos: salida y entrada el
    mismo dia NO es un choque.
    """
    consulta = (
        Reserva.objects
        .filter(unidad_id=unidad_id, fecha_ingreso__lt=egreso, fecha_egreso__gt=ingreso)
        .exclude(estado=Reserva.ESTADO_CANCELADA)
        .select_related("huesped")
    )
    if excluir_pk:
        consulta = consulta.exclude(pk=excluir_pk)
    return list(consulta.order_by("fecha_ingreso"))


def cierres_que_chocan(unidad_id, ingreso, egreso):
    """Cierres de fechas (del departamento o de todo el complejo) que tocan la estadia."""
    return list(
        Cierre.objects
        .filter(Q(unidad_id=unidad_id) | Q(unidad__isnull=True))
        .filter(fecha_desde__lt=egreso, fecha_hasta__gte=ingreso)
        .order_by("fecha_desde")
    )


def buscar_disponibilidad(ingreso, egreso, personas=None, planta_baja=False, deck=False):
    """Devuelve, para cada departamento activo, si esta libre u ocupado en esas fechas.

    Cada resultado es un diccionario con: unidad, estado, motivos (lista de textos)
    y avisos (cosas a tener en cuenta aunque este libre).
    """
    resultados = []
    noches = (egreso - ingreso).days

    for unidad in Unidad.objects.filter(activa=True).order_by("nombre"):
        motivos = []
        avisos = []

        # Filtros pedidos
        descartes = []
        if planta_baja and not unidad.planta_baja:
            descartes.append("No es planta baja.")
        if deck and not unidad.tiene_deck:
            descartes.append("No tiene deck privado.")
        if descartes:
            resultados.append(
                {"unidad": unidad, "estado": DESCARTADO, "motivos": descartes, "avisos": []}
            )
            continue

        # Reservas que se pisan
        for reserva in reservas_que_chocan(unidad.pk, ingreso, egreso):
            motivos.append(
                f"Reservado por {reserva.huesped} del "
                f"{reserva.fecha_ingreso:%d/%m} al {reserva.fecha_egreso:%d/%m}."
            )
        # Cierres de fechas
        cierres = cierres_que_chocan(unidad.pk, ingreso, egreso)
        for cierre in cierres:
            texto = f"Cerrado del {cierre.fecha_desde:%d/%m} al {cierre.fecha_hasta:%d/%m}"
            texto += f" ({cierre.motivo})." if cierre.motivo else "."
            motivos.append(texto)

        if motivos:
            estado = CERRADO if cierres and len(motivos) == len(cierres) else OCUPADO
        else:
            estado = LIBRE
            if noches < 5:
                avisos.append("Menos de 5 noches: al cargar la reserva hay que tildar la excepción de noches.")
            if personas and personas > unidad.capacidad:
                avisos.append(
                    f"Supera la capacidad ({unidad.capacidad}): al cargar la reserva hay que tildar la excepción de personas."
                )

        resultados.append({"unidad": unidad, "estado": estado, "motivos": motivos, "avisos": avisos})

    return resultados
