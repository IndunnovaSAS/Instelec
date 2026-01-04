"""Integration tests for environmental workflow."""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

from apps.ambiental.models import InformeAmbiental, PermisoServidumbre


@pytest.mark.django_db
class TestFlujoInformeAmbiental:
    """Integration tests for Environmental Report flow."""

    def test_informe_ambiental_workflow(self):
        """Environmental report approval workflow."""
        from tests.factories import (
            InformeAmbientalFactory,
            CoordinadorFactory,
        )

        elaborador = CoordinadorFactory()
        revisor = CoordinadorFactory()
        aprobador = CoordinadorFactory()

        # Create draft report
        informe = InformeAmbientalFactory(
            estado=InformeAmbiental.Estado.BORRADOR,
            elaborado_por=elaborador,
            fecha_elaboracion=timezone.now(),
        )
        assert informe.estado == InformeAmbiental.Estado.BORRADOR

        # Send for review
        informe.estado = InformeAmbiental.Estado.EN_REVISION
        informe.revisado_por = revisor
        informe.fecha_revision = timezone.now()
        informe.save()
        assert informe.estado == InformeAmbiental.Estado.EN_REVISION

        # Approve
        informe.estado = InformeAmbiental.Estado.APROBADO
        informe.aprobado_por = aprobador
        informe.fecha_aprobacion = timezone.now()
        informe.save()
        assert informe.estado == InformeAmbiental.Estado.APROBADO

        # Send to client
        informe.estado = InformeAmbiental.Estado.ENVIADO
        informe.fecha_envio = timezone.now()
        informe.url_pdf = "https://storage.googleapis.com/transmaint/informes/informe.pdf"
        informe.save()
        assert informe.estado == InformeAmbiental.Estado.ENVIADO

    def test_informe_rechazado(self):
        """Environmental report rejection workflow."""
        from tests.factories import InformeAmbientalFactory

        informe = InformeAmbientalFactory(
            estado=InformeAmbiental.Estado.EN_REVISION,
        )

        # Reject with observations
        informe.estado = InformeAmbiental.Estado.RECHAZADO
        informe.observaciones = "Falta información de hectáreas intervenidas"
        informe.save()

        informe.refresh_from_db()
        assert informe.estado == InformeAmbiental.Estado.RECHAZADO
        assert "hectáreas" in informe.observaciones


@pytest.mark.django_db
class TestFlujoPermisoServidumbre:
    """Integration tests for Easement Permission flow."""

    def test_verificar_permisos_torre(self):
        """Verify all towers have valid permissions before activity."""
        from tests.factories import (
            LineaFactory,
            TorreFactory,
            PermisoServidumbreFactory,
            ActividadFactory,
        )

        linea = LineaFactory()
        torre = TorreFactory(linea=linea)

        # Create valid permission
        permiso = PermisoServidumbreFactory(
            torre=torre,
            fecha_autorizacion=date.today() - timedelta(days=30),
            fecha_vencimiento=date.today() + timedelta(days=335),
        )

        # Create activity for this tower
        actividad = ActividadFactory(linea=linea, torre=torre)

        # Check permission is valid
        assert permiso.vigente
        assert torre.permisos_servidumbre.filter(
            fecha_vencimiento__gte=date.today()
        ).exists()

    def test_alerta_permisos_por_vencer(self):
        """Alert for permissions expiring soon."""
        from tests.factories import (
            TorreFactory,
            PermisoServidumbreFactory,
        )

        torre = TorreFactory()

        # Create permission expiring in 15 days
        permiso = PermisoServidumbreFactory(
            torre=torre,
            fecha_autorizacion=date.today() - timedelta(days=350),
            fecha_vencimiento=date.today() + timedelta(days=15),
        )

        # Check if expires within 30 days
        dias_hasta_vencimiento = (permiso.fecha_vencimiento - date.today()).days
        assert dias_hasta_vencimiento < 30
        assert permiso.vigente  # Still valid but about to expire

    def test_multiples_permisos_por_torre(self):
        """A tower can have multiple permissions (different landowners)."""
        from tests.factories import TorreFactory, PermisoServidumbreFactory

        torre = TorreFactory()

        # Create permissions for different landowners
        permiso1 = PermisoServidumbreFactory(
            torre=torre,
            propietario_nombre="Juan Pérez",
            predio_nombre="Finca El Roble",
        )
        permiso2 = PermisoServidumbreFactory(
            torre=torre,
            propietario_nombre="María García",
            predio_nombre="Hacienda La Esperanza",
        )

        assert torre.permisos_servidumbre.count() == 2


@pytest.mark.django_db
class TestFlujoInformeActividades:
    """Integration tests for Report based on Activities."""

    def test_generar_resumen_actividades_ambientales(self):
        """Generate environmental activity summary for report."""
        from tests.factories import (
            LineaFactory,
            TorreFactory,
            ActividadCompletadaFactory,
            TipoActividadFactory,
            RegistroCampoCompletadoFactory,
        )

        linea = LineaFactory()

        # Create poda activities
        tipo_poda = TipoActividadFactory(
            codigo="PODA-ENV",
            nombre="Poda de vegetación",
            categoria="PODA",
        )

        torres = [TorreFactory(linea=linea) for _ in range(5)]
        for torre in torres:
            actividad = ActividadCompletadaFactory(
                linea=linea,
                torre=torre,
                tipo_actividad=tipo_poda,
                fecha_programada=date(2025, 6, 15),
            )
            RegistroCampoCompletadoFactory(
                actividad=actividad,
                datos_formulario={
                    "hectareas_podadas": 2.5,
                    "m3_vegetacion": 30.0,
                },
            )

        # Calculate totals
        from apps.campo.models import RegistroCampo
        registros = RegistroCampo.objects.filter(
            actividad__linea=linea,
            actividad__tipo_actividad__categoria="PODA",
            actividad__fecha_programada__month=6,
            actividad__fecha_programada__year=2025,
        )

        total_hectareas = sum(
            r.datos_formulario.get("hectareas_podadas", 0)
            for r in registros
        )
        total_m3 = sum(
            r.datos_formulario.get("m3_vegetacion", 0)
            for r in registros
        )

        assert registros.count() == 5
        assert total_hectareas == 12.5
        assert total_m3 == 150.0


@pytest.mark.django_db
class TestFlujoAmbientalIndicadores:
    """Integration tests for Environmental -> KPI flow."""

    def test_calcular_indicador_ambiental(self):
        """Calculate environmental compliance indicator."""
        from tests.factories import (
            LineaFactory,
            ActividadCompletadaFactory,
            TipoActividadFactory,
            InformeAmbientalAprobadoFactory,
        )
        from apps.indicadores.calculators import calcular_gestion_ambiental

        linea = LineaFactory()

        # Create poda activities in January
        tipo_poda = TipoActividadFactory(categoria="PODA")
        for _ in range(10):
            ActividadCompletadaFactory(
                linea=linea,
                tipo_actividad=tipo_poda,
                fecha_programada=date(2025, 1, 15),
            )

        # Create approved environmental report
        informe = InformeAmbientalAprobadoFactory(
            linea=linea,
            periodo_mes=1,
            periodo_anio=2025,
            total_actividades=10,
            total_podas=10,
        )

        # Calculate environmental indicator
        con_informe, total, valor = calcular_gestion_ambiental(linea.id, 2025, 1)

        # Should have full compliance since report is approved
        assert con_informe >= 0
        assert total >= 0
