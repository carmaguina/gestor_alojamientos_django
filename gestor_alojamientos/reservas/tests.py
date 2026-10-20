from datetime import date
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import TestCase

from alojamientos.models import Unidad

from .models import Cierre, Huesped, Reserva


class ValidacionesReservaTests(TestCase):
    """Prueba las reglas del negocio de Reserva.clean()."""

    def setUp(self):
        self.depto_a = Unidad.objects.create(nombre="Departamento A", capacidad=4)
        self.depto_b = Unidad.objects.create(nombre="Departamento B", capacidad=4)
        self.huesped = Huesped.objects.create(nombre="Ana", apellido="Prueba")

    def nueva(self, ingreso, egreso, **extra):
        """Arma una reserva (sin guardarla) con valores razonables por defecto."""
        datos = dict(
            unidad=self.depto_a,
            huesped=self.huesped,
            fecha_ingreso=ingreso,
            fecha_egreso=egreso,
            cantidad_personas=2,
            estado=Reserva.ESTADO_RESERVADA,
        )
        datos.update(extra)
        return Reserva(**datos)

    def guardada(self, ingreso, egreso, **extra):
        reserva = self.nueva(ingreso, egreso, **extra)
        reserva.save()
        return reserva

    # --- Reglas 1 y 2: fechas y noches ---

    def test_egreso_debe_ser_posterior(self):
        with self.assertRaises(ValidationError):
            self.nueva(date(2027, 1, 10), date(2027, 1, 10)).full_clean()

    def test_minimo_cinco_noches(self):
        with self.assertRaises(ValidationError):
            self.nueva(date(2027, 1, 10), date(2027, 1, 13)).full_clean()

    def test_cinco_noches_es_valido(self):
        self.nueva(date(2027, 1, 10), date(2027, 1, 15)).full_clean()

    def test_excepcion_permite_una_noche(self):
        self.nueva(date(2027, 1, 10), date(2027, 1, 11), excepcion_noches=True).full_clean()

    # --- Regla 3: personas ---

    def test_cinco_personas_sin_excepcion(self):
        with self.assertRaises(ValidationError):
            self.nueva(date(2027, 1, 10), date(2027, 1, 17), cantidad_personas=5).full_clean()

    def test_cinco_personas_con_excepcion(self):
        self.nueva(date(2027, 1, 10), date(2027, 1, 17),
                   cantidad_personas=5, excepcion_personas=True).full_clean()

    def test_siete_personas_con_excepcion(self):
        with self.assertRaises(ValidationError):
            self.nueva(date(2027, 1, 10), date(2027, 1, 17),
                       cantidad_personas=7, excepcion_personas=True).full_clean()

    def test_personas_vacio_no_rompe(self):
        reserva = self.nueva(date(2027, 1, 10), date(2027, 1, 17), cantidad_personas=None)
        reserva.clean()  # no debe lanzar TypeError

    # --- Regla 4: superposicion ---

    def test_superposicion_parcial(self):
        self.guardada(date(2027, 1, 10), date(2027, 1, 17))
        with self.assertRaises(ValidationError):
            self.nueva(date(2027, 1, 15), date(2027, 1, 22)).full_clean()

    def test_superposicion_incluida(self):
        self.guardada(date(2027, 1, 10), date(2027, 1, 17))
        with self.assertRaises(ValidationError):
            self.nueva(date(2027, 1, 12), date(2027, 1, 14), excepcion_noches=True).full_clean()

    def test_superposicion_que_contiene(self):
        self.guardada(date(2027, 1, 10), date(2027, 1, 17))
        with self.assertRaises(ValidationError):
            self.nueva(date(2027, 1, 8), date(2027, 1, 20)).full_clean()

    def test_misma_fecha_de_salida_y_entrada_es_valido(self):
        self.guardada(date(2027, 1, 10), date(2027, 1, 17))
        self.nueva(date(2027, 1, 17), date(2027, 1, 24)).full_clean()   # entra el dia que se va
        self.nueva(date(2027, 1, 3), date(2027, 1, 10)).full_clean()    # sale el dia que entra

    def test_otro_departamento_no_choca(self):
        self.guardada(date(2027, 1, 10), date(2027, 1, 17))
        self.nueva(date(2027, 1, 10), date(2027, 1, 17), unidad=self.depto_b).full_clean()

    def test_reserva_cancelada_no_bloquea(self):
        self.guardada(date(2027, 1, 10), date(2027, 1, 17), estado=Reserva.ESTADO_CANCELADA)
        self.nueva(date(2027, 1, 10), date(2027, 1, 17)).full_clean()

    def test_editar_una_reserva_no_choca_consigo_misma(self):
        reserva = self.guardada(date(2027, 1, 10), date(2027, 1, 17))
        reserva.cantidad_personas = 3
        reserva.full_clean()

    # --- Regla 5: sena ---

    def test_sena_menor_al_cincuenta_por_ciento(self):
        with self.assertRaises(ValidationError):
            self.nueva(date(2027, 1, 10), date(2027, 1, 17),
                       monto_total=Decimal("1000"), monto_senia=Decimal("400")).full_clean()

    def test_sena_del_cincuenta_por_ciento(self):
        self.nueva(date(2027, 1, 10), date(2027, 1, 17),
                   monto_total=Decimal("1000"), monto_senia=Decimal("500")).full_clean()

    def test_sena_se_calcula_sobre_el_total_con_descuento(self):
        # total 1000 con 10% de descuento = 900; el 50% es 450
        base = dict(monto_total=Decimal("1000"), descuento_porcentaje=Decimal("10"))
        self.nueva(date(2027, 1, 10), date(2027, 1, 17),
                   monto_senia=Decimal("450"), **base).full_clean()
        with self.assertRaises(ValidationError):
            self.nueva(date(2027, 1, 10), date(2027, 1, 17),
                       monto_senia=Decimal("440"), **base).full_clean()

    # --- Regla 6: cierres de fechas ---

    def test_cierre_de_todo_el_complejo(self):
        Cierre.objects.create(fecha_desde=date(2027, 1, 1), fecha_hasta=date(2027, 1, 31))
        with self.assertRaises(ValidationError):
            self.nueva(date(2027, 1, 10), date(2027, 1, 17)).full_clean()

    def test_cierre_de_otro_departamento_no_afecta(self):
        Cierre.objects.create(unidad=self.depto_b,
                              fecha_desde=date(2027, 1, 1), fecha_hasta=date(2027, 1, 31))
        self.nueva(date(2027, 1, 10), date(2027, 1, 17)).full_clean()

    def test_reserva_justo_despues_del_cierre(self):
        Cierre.objects.create(fecha_desde=date(2027, 1, 1), fecha_hasta=date(2027, 1, 9))
        self.nueva(date(2027, 1, 10), date(2027, 1, 17)).full_clean()

    # --- Datos calculados ---

    def test_datos_calculados(self):
        reserva = self.nueva(
            date(2027, 1, 10), date(2027, 1, 17),
            monto_total=Decimal("700000"), descuento_porcentaje=Decimal("10"),
            monto_senia=Decimal("350000"),
        )
        self.assertEqual(reserva.noches, 7)
        self.assertEqual(reserva.total_final, Decimal("630000"))
        self.assertEqual(reserva.saldo_pendiente, Decimal("280000"))
