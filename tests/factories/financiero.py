"""Factories for financiero app."""

import factory
from datetime import date, timedelta
from decimal import Decimal

from apps.financiero.models import CostoRecurso, Presupuesto, EjecucionCosto, CicloFacturacion
from tests.factories.lineas import LineaFactory
from tests.factories.actividades import ActividadCompletadaFactory


class CostoRecursoFactory(factory.django.DjangoModelFactory):
    """Factory for CostoRecurso model."""

    class Meta:
        model = CostoRecurso

    tipo = factory.Iterator([
        CostoRecurso.TipoRecurso.DIA_HOMBRE,
        CostoRecurso.TipoRecurso.VEHICULO,
        CostoRecurso.TipoRecurso.VIATICO,
    ])
    descripcion = factory.Faker("sentence", nb_words=3, locale="es_CO")
    costo_unitario = factory.LazyFunction(
        lambda: Decimal(str(round(factory.Faker._get_faker().pyfloat(min_value=50000, max_value=500000), 2)))
    )
    unidad = factory.Iterator(["DIA", "HORA", "UNIDAD"])
    vigencia_desde = factory.LazyFunction(lambda: date.today() - timedelta(days=365))
    vigencia_hasta = None
    activo = True


class CostoDiaHombreFactory(CostoRecursoFactory):
    """Factory for day-man cost."""

    tipo = CostoRecurso.TipoRecurso.DIA_HOMBRE
    descripcion = "Día hombre liniero"
    costo_unitario = Decimal("120000.00")
    unidad = "DIA"


class CostoVehiculoFactory(CostoRecursoFactory):
    """Factory for vehicle cost."""

    tipo = CostoRecurso.TipoRecurso.VEHICULO
    descripcion = "Día camioneta 4x4"
    costo_unitario = Decimal("180000.00")
    unidad = "DIA"


class PresupuestoFactory(factory.django.DjangoModelFactory):
    """Factory for Presupuesto model."""

    class Meta:
        model = Presupuesto

    anio = factory.LazyFunction(lambda: date.today().year)
    mes = factory.LazyFunction(lambda: date.today().month)
    linea = factory.SubFactory(LineaFactory)
    estado = Presupuesto.Estado.PROYECTADO
    dias_hombre_planeados = factory.Faker("random_int", min=20, max=100)
    costo_dias_hombre = factory.LazyFunction(
        lambda: Decimal(str(round(factory.Faker._get_faker().pyfloat(min_value=2000000, max_value=15000000), 2)))
    )
    dias_vehiculo_planeados = factory.Faker("random_int", min=10, max=50)
    costo_vehiculos = factory.LazyFunction(
        lambda: Decimal(str(round(factory.Faker._get_faker().pyfloat(min_value=1000000, max_value=8000000), 2)))
    )
    viaticos_planeados = factory.LazyFunction(
        lambda: Decimal(str(round(factory.Faker._get_faker().pyfloat(min_value=500000, max_value=3000000), 2)))
    )
    otros_costos = factory.LazyFunction(
        lambda: Decimal(str(round(factory.Faker._get_faker().pyfloat(min_value=100000, max_value=1000000), 2)))
    )

    @factory.lazy_attribute
    def total_presupuestado(self):
        return (
            self.costo_dias_hombre +
            self.costo_vehiculos +
            self.viaticos_planeados +
            self.otros_costos
        )

    total_ejecutado = Decimal("0.00")
    facturacion_esperada = factory.LazyAttribute(
        lambda obj: obj.total_presupuestado * Decimal("1.15")
    )


class PresupuestoAprobadoFactory(PresupuestoFactory):
    """Factory for approved budget."""

    estado = Presupuesto.Estado.APROBADO


class PresupuestoEnEjecucionFactory(PresupuestoFactory):
    """Factory for budget in execution."""

    estado = Presupuesto.Estado.EN_EJECUCION

    @factory.lazy_attribute
    def total_ejecutado(self):
        return self.total_presupuestado * Decimal("0.6")


class EjecucionCostoFactory(factory.django.DjangoModelFactory):
    """Factory for EjecucionCosto model."""

    class Meta:
        model = EjecucionCosto

    presupuesto = factory.SubFactory(PresupuestoEnEjecucionFactory)
    actividad = factory.SubFactory(ActividadCompletadaFactory)
    concepto = factory.Faker("sentence", nb_words=4, locale="es_CO")
    tipo_recurso = factory.Iterator([
        CostoRecurso.TipoRecurso.DIA_HOMBRE,
        CostoRecurso.TipoRecurso.VEHICULO,
        CostoRecurso.TipoRecurso.VIATICO,
    ])
    cantidad = factory.LazyFunction(
        lambda: Decimal(str(round(factory.Faker._get_faker().pyfloat(min_value=1, max_value=10), 2)))
    )
    costo_unitario = factory.LazyFunction(
        lambda: Decimal(str(round(factory.Faker._get_faker().pyfloat(min_value=50000, max_value=200000), 2)))
    )
    fecha = factory.LazyFunction(lambda: date.today())

    @factory.lazy_attribute
    def costo_total(self):
        return self.cantidad * self.costo_unitario


class CicloFacturacionFactory(factory.django.DjangoModelFactory):
    """Factory for CicloFacturacion model."""

    class Meta:
        model = CicloFacturacion

    presupuesto = factory.SubFactory(PresupuestoEnEjecucionFactory)
    estado = CicloFacturacion.Estado.INFORME_GENERADO
    fecha_informe = factory.LazyFunction(lambda: date.today())
    monto_facturado = Decimal("0.00")
    monto_pagado = Decimal("0.00")


class CicloFacturacionPagadoFactory(CicloFacturacionFactory):
    """Factory for paid billing cycle."""

    estado = CicloFacturacion.Estado.PAGO_RECIBIDO
    fecha_informe = factory.LazyFunction(lambda: date.today() - timedelta(days=60))
    fecha_validacion = factory.LazyFunction(lambda: date.today() - timedelta(days=55))
    fecha_orden = factory.LazyFunction(lambda: date.today() - timedelta(days=45))
    fecha_factura = factory.LazyFunction(lambda: date.today() - timedelta(days=40))
    fecha_pago = factory.LazyFunction(lambda: date.today() - timedelta(days=5))
    monto_facturado = factory.LazyAttribute(lambda obj: obj.presupuesto.facturacion_esperada)
    monto_pagado = factory.LazyAttribute(lambda obj: obj.monto_facturado)
    numero_factura = factory.LazyFunction(
        lambda: f"FE-{factory.Faker._get_faker().random_int(min=1000, max=9999)}"
    )
    numero_orden = factory.LazyFunction(
        lambda: f"OE-{factory.Faker._get_faker().random_int(min=1000, max=9999)}"
    )
