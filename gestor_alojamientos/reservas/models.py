from decimal import Decimal

from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q

from alojamientos.models import Unidad


class Huesped(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    notas = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    class Meta:
        verbose_name = "Huésped"
        verbose_name_plural = "Huéspedes"


class Reserva(models.Model):
    ESTADO_CONSULTA = "consulta"
    ESTADO_PRE_RESERVA = "pre_reserva"
    ESTADO_RESERVADA = "reservada"
    ESTADO_SENIADA = "seniada"
    ESTADO_CANCELADA = "cancelada"
    ESTADO_FINALIZADA = "finalizada"

    ESTADOS = [
        (ESTADO_CONSULTA, "Consulta"),
        (ESTADO_PRE_RESERVA, "Pre-reserva"),
        (ESTADO_RESERVADA, "Reservada"),
        (ESTADO_SENIADA, "Señada"),
        (ESTADO_CANCELADA, "Cancelada"),
        (ESTADO_FINALIZADA, "Finalizada"),
    ]

    # Opciones para el medio de pago de la sena
    MEDIO_EFECTIVO = "efectivo"
    MEDIO_TRANSFERENCIA = "transferencia"
    MEDIO_MERCADO_PAGO = "mercado_pago"

    MEDIOS_PAGO = [
        (MEDIO_EFECTIVO, "Efectivo"),
        (MEDIO_TRANSFERENCIA, "Transferencia"),
        (MEDIO_MERCADO_PAGO, "Mercado Pago"),
    ]

    unidad = models.ForeignKey(Unidad, on_delete=models.PROTECT, related_name="reservas")
    huesped = models.ForeignKey(Huesped, on_delete=models.PROTECT, related_name="reservas")
    fecha_ingreso = models.DateField()
    fecha_egreso = models.DateField()
    cantidad_personas = models.PositiveIntegerField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default=ESTADO_CONSULTA)
    monto_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    monto_senia = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    observaciones = models.TextField(blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # --- NUEVO: excepciones a las reglas habituales ---
    # Una casilla (BooleanField) es un "si / no". default=False significa
    # que, si no la tildas, la regla normal se aplica.
    excepcion_noches = models.BooleanField(
        "Excepción de noches mínimas",
        default=False,
        help_text="Tildar si la estadía es de menos de 5 noches.",
    )
    excepcion_personas = models.BooleanField(
        "Excepción de personas",
        default=False,
        help_text="Tildar si son más de 4 personas (hasta 6 adultos).",
    )
    excepcion_senia = models.BooleanField(
        "Excepción de seña",
        default=False,
        help_text="Tildar si la seña es menor al 50% del total.",
    )
    # blank=True: el campo puede quedar vacío (solo se llena si hay excepción)
    motivo_excepcion = models.TextField("Motivo de la excepción", blank=True)

    # --- NUEVO: mascota ---
    lleva_mascota = models.BooleanField("Lleva mascota", default=False)
    detalle_mascota = models.CharField(
        "Detalle de la mascota", max_length=200, blank=True,
        help_text="Cuántas, tamaño, raza, etc.",
    )

    # --- NUEVO: dinero ---
    # Un porcentaje de 0 a 100. Los validadores impiden cargar -5 o 250.
    descuento_porcentaje = models.DecimalField(
        "Descuento (%)",
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    medio_pago = models.CharField(
        "Medio de pago de la seña",
        max_length=20,
        choices=MEDIOS_PAGO,
        blank=True,
    )

    def __str__(self):
        return f"{self.huesped} - {self.unidad} ({self.fecha_ingreso} a {self.fecha_egreso})"

    # --- NUEVO: validaciones (paso B) ---
    # clean() se ejecuta al guardar. Si algo no cumple las reglas, juntamos
    # los errores en un diccionario {campo: mensaje} y los mostramos todos.
    def clean(self):
        errores = {}

        if self.fecha_ingreso and self.fecha_egreso:
            # Regla 1: el egreso tiene que ser posterior al ingreso
            if self.fecha_egreso <= self.fecha_ingreso:
                errores["fecha_egreso"] = "El egreso debe ser posterior al ingreso."
            else:
                # Regla 2: minimo 5 noches (con la excepcion tildada, desde 1)
                minimo = 1 if self.excepcion_noches else 5
                if self.noches < minimo:
                    errores["fecha_egreso"] = (
                        f"La estadía mínima es de {minimo} noches "
                        f"(esta reserva tiene {self.noches})."
                    )

        # Regla 3: maximo de personas (4; con la excepcion tildada, 6).
        # El "is not None" evita un error si el campo todavia esta vacio.
        if self.cantidad_personas is not None:
            maximo = 6 if self.excepcion_personas else 4
            if self.cantidad_personas > maximo:
                errores["cantidad_personas"] = (
                    f"El máximo es de {maximo} personas"
                    + ("" if self.excepcion_personas else "; para más, tildá la excepción.")
                )

        # Las reglas que siguen necesitan departamento y fechas completos
        if self.unidad_id and self.fecha_ingreso and self.fecha_egreso \
                and self.fecha_egreso > self.fecha_ingreso:

            # Regla 4: no pisarse con otra reserva del mismo departamento.
            # Hay conflicto si la otra empieza ANTES de que esta termine
            # y termina DESPUES de que esta empiece (< y > estrictos: asi
            # se permite salida y entrada el mismo dia).
            if self.estado != self.ESTADO_CANCELADA:
                choque = (
                    Reserva.objects
                    .filter(
                        unidad_id=self.unidad_id,
                        fecha_ingreso__lt=self.fecha_egreso,
                        fecha_egreso__gt=self.fecha_ingreso,
                    )
                    .exclude(estado=self.ESTADO_CANCELADA)
                    .exclude(pk=self.pk)
                    .first()
                )
                if choque:
                    errores["fecha_ingreso"] = (
                        f"Este departamento ya está reservado del "
                        f"{choque.fecha_ingreso:%d/%m/%Y} al {choque.fecha_egreso:%d/%m/%Y}."
                    )

            # Regla 6: no caer en un cierre de fechas (de este departamento
            # o de todo el complejo, que es cuando unidad queda vacia).
            cierre = (
                Cierre.objects
                .filter(Q(unidad_id=self.unidad_id) | Q(unidad__isnull=True))
                .filter(fecha_desde__lt=self.fecha_egreso, fecha_hasta__gte=self.fecha_ingreso)
                .first()
            )
            if cierre:
                errores["fecha_ingreso"] = (
                    f"Hay un cierre de fechas del "
                    f"{cierre.fecha_desde:%d/%m/%Y} al {cierre.fecha_hasta:%d/%m/%Y}."
                )

        # Regla 5: la sena debe ser al menos el 50% del total (con descuento),
        # salvo que este tildada la excepcion de sena.
        total = self.total_final
        if total is not None and self.monto_senia is not None and not self.excepcion_senia:
            if self.monto_senia < total / 2:
                errores["monto_senia"] = (
                    f"La seña debe ser al menos el 50% del total (${total / 2:,.2f}). "
                    "Si aceptás menos, tildá la excepción de seña."
                )

        if errores:
            raise ValidationError(errores)

    # --- NUEVO: datos calculados ---
    # Una @property se usa como si fuera un campo (reserva.noches),
    # pero no se guarda en la base: se calcula cada vez.
    @property
    def noches(self):
        if self.fecha_ingreso and self.fecha_egreso:
            return (self.fecha_egreso - self.fecha_ingreso).days
        return None

    @property
    def total_final(self):
        """Monto total ya con el descuento aplicado."""
        if self.monto_total is None:
            return None
        return self.monto_total * (Decimal(100) - self.descuento_porcentaje) / Decimal(100)

    @property
    def saldo_pendiente(self):
        """Lo que falta cobrar: total final menos la seña."""
        total = self.total_final
        if total is None:
            return None
        return total - (self.monto_senia or Decimal(0))

    class Meta:
        verbose_name = "Reserva"
        verbose_name_plural = "Reservas"
        ordering = ["-fecha_ingreso"]


class Cierre(models.Model):
    """Un rango de fechas en el que no se aceptan reservas (por ejemplo,
    el complejo en pausa en agosto y septiembre, o un departamento en arreglos)."""

    # null=True, blank=True: si se deja vacío, el cierre vale para TODO el complejo.
    unidad = models.ForeignKey(
        Unidad,
        on_delete=models.CASCADE,
        related_name="cierres",
        null=True,
        blank=True,
        help_text="Dejar vacío para cerrar todo el complejo.",
    )
    fecha_desde = models.DateField("Desde")
    fecha_hasta = models.DateField("Hasta")
    motivo = models.CharField(max_length=200, blank=True)

    def __str__(self):
        donde = self.unidad if self.unidad else "Todo el complejo"
        return f"{donde}: {self.fecha_desde} a {self.fecha_hasta}"

    class Meta:
        verbose_name = "Cierre de fechas"
        verbose_name_plural = "Cierres de fechas"
        ordering = ["-fecha_desde"]
