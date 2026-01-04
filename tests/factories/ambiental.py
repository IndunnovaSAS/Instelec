"""Factories for ambiental app."""

import factory
from datetime import date, timedelta
from decimal import Decimal
from django.utils import timezone

from apps.ambiental.models import InformeAmbiental, PermisoServidumbre
from tests.factories.lineas import LineaFactory, TorreFactory
from tests.factories.usuarios import CoordinadorFactory


class InformeAmbientalFactory(factory.django.DjangoModelFactory):
    """Factory for InformeAmbiental model."""

    class Meta:
        model = InformeAmbiental

    periodo_mes = factory.LazyFunction(lambda: date.today().month)
    periodo_anio = factory.LazyFunction(lambda: date.today().year)
    linea = factory.SubFactory(LineaFactory)
    estado = InformeAmbiental.Estado.BORRADOR
    total_actividades = factory.Faker("random_int", min=10, max=50)
    total_podas = factory.Faker("random_int", min=5, max=30)
    hectareas_intervenidas = factory.LazyFunction(
        lambda: Decimal(str(round(factory.Faker._get_faker().pyfloat(min_value=1.0, max_value=50.0), 2)))
    )
    m3_vegetacion = factory.LazyFunction(
        lambda: Decimal(str(round(factory.Faker._get_faker().pyfloat(min_value=10.0, max_value=500.0), 2)))
    )
    elaborado_por = factory.SubFactory(CoordinadorFactory)
    observaciones = factory.Faker("paragraph", locale="es_CO")


class InformeAmbientalAprobadoFactory(InformeAmbientalFactory):
    """Factory for approved environmental report."""

    estado = InformeAmbiental.Estado.APROBADO
    revisado_por = factory.SubFactory(CoordinadorFactory)
    aprobado_por = factory.SubFactory(CoordinadorFactory)
    fecha_elaboracion = factory.LazyFunction(
        lambda: timezone.now() - timedelta(days=5)
    )
    fecha_revision = factory.LazyFunction(
        lambda: timezone.now() - timedelta(days=3)
    )
    fecha_aprobacion = factory.LazyFunction(
        lambda: timezone.now() - timedelta(days=1)
    )


class PermisoServidumbreFactory(factory.django.DjangoModelFactory):
    """Factory for PermisoServidumbre model."""

    class Meta:
        model = PermisoServidumbre

    torre = factory.SubFactory(TorreFactory)
    propietario_nombre = factory.Faker("name", locale="es_CO")
    propietario_documento = factory.LazyFunction(
        lambda: str(factory.Faker._get_faker().random_int(min=10000000, max=99999999))
    )
    propietario_telefono = factory.LazyFunction(
        lambda: f"+57 3{factory.Faker._get_faker().random_int(min=100000000, max=199999999)}"
    )
    predio_nombre = factory.Faker("street_name", locale="es_CO")
    predio_matricula = factory.LazyFunction(
        lambda: f"050-{factory.Faker._get_faker().random_int(min=100000, max=999999)}"
    )
    fecha_autorizacion = factory.LazyFunction(lambda: date.today() - timedelta(days=30))
    fecha_vencimiento = factory.LazyFunction(lambda: date.today() + timedelta(days=335))
    actividades_autorizadas = "Poda de vegetación, Inspección visual, Cambio de herrajes"


class PermisoServidumbreVencidoFactory(PermisoServidumbreFactory):
    """Factory for expired easement permission."""

    fecha_autorizacion = factory.LazyFunction(lambda: date.today() - timedelta(days=400))
    fecha_vencimiento = factory.LazyFunction(lambda: date.today() - timedelta(days=35))
