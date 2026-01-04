"""Factories for indicadores app."""

import factory
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone

from apps.indicadores.models import Indicador, MedicionIndicador, ActaSeguimiento
from tests.factories.lineas import LineaFactory


class IndicadorFactory(factory.django.DjangoModelFactory):
    """Factory for Indicador model."""

    class Meta:
        model = Indicador

    codigo = factory.Sequence(lambda n: f"IND-{n:03d}")
    nombre = factory.Iterator([
        "Gestión de Mantenimiento",
        "Ejecución de Mantenimiento",
        "Cumplimiento Ambiental",
        "Seguridad Industrial",
        "Calidad de Información",
        "Cumplimiento de Cronograma",
    ])
    descripcion = factory.Faker("paragraph", locale="es_CO")
    categoria = factory.Iterator([
        Indicador.Categoria.GESTION,
        Indicador.Categoria.EJECUCION,
        Indicador.Categoria.AMBIENTAL,
        Indicador.Categoria.SEGURIDAD,
        Indicador.Categoria.CALIDAD,
    ])
    formula = factory.Faker("sentence", locale="es_CO")
    unidad = "%"
    meta = Decimal("95.00")
    umbral_alerta = Decimal("80.00")
    peso_ponderacion = Decimal("1.00")
    activo = True


class IndicadorGestionFactory(IndicadorFactory):
    """Factory for management indicator."""

    codigo = factory.Sequence(lambda n: f"GEST-{n:03d}")
    nombre = "Gestión de Mantenimiento"
    categoria = Indicador.Categoria.GESTION
    formula = "(Actividades Programadas / Actividades Ejecutadas) * 100"
    meta = Decimal("95.00")
    umbral_alerta = Decimal("85.00")


class IndicadorEjecucionFactory(IndicadorFactory):
    """Factory for execution indicator."""

    codigo = factory.Sequence(lambda n: f"EJEC-{n:03d}")
    nombre = "Ejecución de Mantenimiento"
    categoria = Indicador.Categoria.EJECUCION
    formula = "(Actividades Completadas a tiempo / Actividades Programadas) * 100"
    meta = Decimal("90.00")
    umbral_alerta = Decimal("80.00")


class IndicadorSeguridadFactory(IndicadorFactory):
    """Factory for security indicator."""

    codigo = factory.Sequence(lambda n: f"SEG-{n:03d}")
    nombre = "Seguridad Industrial"
    categoria = Indicador.Categoria.SEGURIDAD
    formula = "(Días sin accidentes / Días laborables) * 100"
    meta = Decimal("100.00")
    umbral_alerta = Decimal("95.00")


class MedicionIndicadorFactory(factory.django.DjangoModelFactory):
    """Factory for MedicionIndicador model."""

    class Meta:
        model = MedicionIndicador

    indicador = factory.SubFactory(IndicadorFactory)
    linea = factory.SubFactory(LineaFactory)
    anio = factory.LazyFunction(lambda: date.today().year)
    mes = factory.LazyFunction(lambda: date.today().month)
    valor_numerador = factory.LazyFunction(
        lambda: Decimal(str(round(factory.Faker._get_faker().pyfloat(min_value=80, max_value=100), 2)))
    )
    valor_denominador = Decimal("100.00")

    @factory.lazy_attribute
    def valor_calculado(self):
        if self.valor_denominador > 0:
            return (self.valor_numerador / self.valor_denominador) * 100
        return Decimal("0.00")

    @factory.lazy_attribute
    def cumple_meta(self):
        return self.valor_calculado >= self.indicador.meta

    @factory.lazy_attribute
    def en_alerta(self):
        return self.valor_calculado < self.indicador.umbral_alerta


class MedicionCumpleMeta(MedicionIndicadorFactory):
    """Factory for measurement that meets goal."""

    valor_numerador = Decimal("98.00")
    valor_denominador = Decimal("100.00")


class MedicionEnAlerta(MedicionIndicadorFactory):
    """Factory for measurement in alert."""

    valor_numerador = Decimal("75.00")
    valor_denominador = Decimal("100.00")


class ActaSeguimientoFactory(factory.django.DjangoModelFactory):
    """Factory for ActaSeguimiento model."""

    class Meta:
        model = ActaSeguimiento

    linea = factory.SubFactory(LineaFactory)
    anio = factory.LazyFunction(lambda: date.today().year)
    mes = factory.LazyFunction(lambda: date.today().month)
    fecha_reunion = factory.LazyFunction(lambda: date.today() - timedelta(days=5))
    estado = ActaSeguimiento.Estado.BORRADOR
    asistentes_instelec = factory.Faker("name", locale="es_CO")
    asistentes_cliente = factory.Faker("name", locale="es_CO")
    resumen_indicadores = factory.LazyFunction(lambda: {
        "gestion": 95.5,
        "ejecucion": 92.0,
        "ambiental": 98.0,
        "seguridad": 100.0,
        "calidad": 94.5,
    })
    compromisos = factory.Faker("paragraph", locale="es_CO")
    observaciones = factory.Faker("paragraph", locale="es_CO")


class ActaSeguimientoFirmadaFactory(ActaSeguimientoFactory):
    """Factory for signed meeting minutes."""

    estado = ActaSeguimiento.Estado.FIRMADA
    url_acta_firmada = factory.LazyAttribute(
        lambda obj: f"https://storage.googleapis.com/transmaint/actas/{obj.linea.codigo}/{obj.mes}-{obj.anio}/acta_firmada.pdf"
    )
