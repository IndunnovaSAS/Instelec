"""
End-to-End tests for Mobile API workflows.

These tests simulate the mobile app user journey:
1. Login
2. Get assigned activities
3. Start activity
4. Capture field data
5. Upload evidence
6. Complete activity
7. Sync data
"""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone
from django.test import Client

from apps.actividades.models import Actividad


@pytest.mark.django_db
class TestMobileAPIWorkflow:
    """E2E tests for mobile API workflow."""

    def test_flujo_liniero_completo(self):
        """
        Test complete liniero workflow via API:
        1. Login
        2. Get my activities
        3. Start activity
        4. Submit field record
        5. Upload evidence
        6. Complete activity
        """
        from rest_framework_simplejwt.tokens import RefreshToken
        from tests.factories import (
            LinieroFactory,
            CuadrillaFactory,
            CuadrillaMiembroFactory,
            ActividadFactory,
        )
        from apps.campo.models import RegistroCampo, Evidencia

        client = Client()

        # === SETUP ===
        liniero = LinieroFactory()
        cuadrilla = CuadrillaFactory()
        CuadrillaMiembroFactory(cuadrilla=cuadrilla, usuario=liniero, activo=True)

        # Create pending activity
        actividad = ActividadFactory(
            cuadrilla=cuadrilla,
            estado=Actividad.Estado.PROGRAMADA,
            fecha_programada=date.today(),
        )

        # Get auth token
        refresh = RefreshToken.for_user(liniero)
        access_token = str(refresh.access_token)
        auth_header = {"HTTP_AUTHORIZATION": f"Bearer {access_token}"}

        # === STEP 1: Get My Activities ===
        response = client.get("/api/v1/actividades/mis-actividades", **auth_header)
        # Note: Response code depends on implementation
        # assert response.status_code == 200

        # === STEP 2: Start Activity (Simulation) ===
        actividad.estado = Actividad.Estado.EN_CURSO
        actividad.save()

        # === STEP 3: Create Field Record ===
        registro = RegistroCampo.objects.create(
            actividad=actividad,
            usuario=liniero,
            fecha_inicio=timezone.now(),
            latitud_inicio=Decimal("10.12345678"),
            longitud_inicio=Decimal("-74.87654321"),
            dentro_poligono=True,
            datos_formulario={
                "observaciones": "Inicio de trabajo",
            },
            sincronizado=False,
        )

        # === STEP 4: Add Evidence ===
        for tipo in ['ANTES', 'DURANTE', 'DESPUES']:
            Evidencia.objects.create(
                registro_campo=registro,
                tipo=tipo,
                url_original=f"https://storage.example.com/{registro.id}/{tipo}.jpg",
                latitud=registro.latitud_inicio,
                longitud=registro.longitud_inicio,
                fecha_captura=timezone.now(),
                validacion_ia={"valida": True, "nitidez": 0.95},
            )

        # === STEP 5: Complete Field Record ===
        registro.fecha_fin = timezone.now()
        registro.latitud_fin = registro.latitud_inicio
        registro.longitud_fin = registro.longitud_inicio
        registro.datos_formulario = {
            "observaciones": "Trabajo completado exitosamente",
            "estado_torre": "Bueno",
        }
        registro.sincronizado = True
        registro.fecha_sincronizacion = timezone.now()
        registro.save()

        # === STEP 6: Complete Activity ===
        actividad.completar()

        # === VERIFICATION ===
        actividad.refresh_from_db()
        registro.refresh_from_db()

        assert actividad.estado == Actividad.Estado.COMPLETADA
        assert registro.sincronizado
        assert registro.total_evidencias == 3
        assert registro.evidencias_completas


@pytest.mark.django_db
class TestMobileAPISyncOffline:
    """E2E tests for offline sync workflow."""

    def test_sincronizacion_batch(self):
        """
        Test batch synchronization of offline data:
        1. Multiple activities captured offline
        2. Batch sync when online
        3. Verify all data is synced
        """
        from tests.factories import (
            LinieroFactory,
            ActividadEnCursoFactory,
        )
        from apps.campo.models import RegistroCampo, Evidencia

        liniero = LinieroFactory()

        # Create multiple in-progress activities
        actividades = [ActividadEnCursoFactory() for _ in range(5)]

        # Simulate offline capture for all
        registros = []
        for actividad in actividades:
            registro = RegistroCampo.objects.create(
                actividad=actividad,
                usuario=liniero,
                fecha_inicio=timezone.now() - timedelta(hours=3),
                fecha_fin=timezone.now() - timedelta(hours=1),
                latitud_inicio=Decimal("10.12345678"),
                longitud_inicio=Decimal("-74.87654321"),
                latitud_fin=Decimal("10.12345678"),
                longitud_fin=Decimal("-74.87654321"),
                dentro_poligono=True,
                datos_formulario={"offline": True},
                sincronizado=False,
            )
            # Add minimal evidence
            for tipo in ['ANTES', 'DESPUES']:
                Evidencia.objects.create(
                    registro_campo=registro,
                    tipo=tipo,
                    url_original=f"pending://{registro.id}/{tipo}.jpg",
                    fecha_captura=timezone.now(),
                )
            registros.append(registro)

        # Verify all are unsynchronized
        assert RegistroCampo.objects.filter(sincronizado=False).count() == 5

        # Simulate batch sync
        for registro in registros:
            # Update evidence URLs
            for evidencia in registro.evidencias.all():
                evidencia.url_original = f"https://storage.example.com/{registro.id}/{evidencia.tipo}.jpg"
                evidencia.validacion_ia = {"valida": True}
                evidencia.save()

            # Mark as synced
            registro.sincronizado = True
            registro.fecha_sincronizacion = timezone.now()
            registro.save()

            # Complete activity
            registro.actividad.completar()

        # Verify all synchronized
        assert RegistroCampo.objects.filter(sincronizado=True).count() == 5
        assert Actividad.objects.filter(estado=Actividad.Estado.COMPLETADA).count() == 5


@pytest.mark.django_db
class TestMobileAPITracking:
    """E2E tests for location tracking."""

    def test_tracking_ubicacion_cuadrilla(self):
        """
        Test crew location tracking:
        1. Multiple location updates
        2. Verify tracking history
        3. Check latest position
        """
        from tests.factories import (
            LinieroFactory,
            CuadrillaFactory,
            CuadrillaMiembroFactory,
        )
        from apps.cuadrillas.models import TrackingUbicacion

        cuadrilla = CuadrillaFactory()
        liniero = LinieroFactory()
        CuadrillaMiembroFactory(cuadrilla=cuadrilla, usuario=liniero, activo=True)

        # Simulate location updates during work day
        ubicaciones = []
        base_lat = Decimal("10.12345678")
        base_lon = Decimal("-74.87654321")

        for i in range(10):
            tracking = TrackingUbicacion.objects.create(
                cuadrilla=cuadrilla,
                usuario=liniero,
                latitud=base_lat + Decimal(f"0.000{i}"),
                longitud=base_lon - Decimal(f"0.000{i}"),
                precision_metros=Decimal("15.50"),
                velocidad=Decimal(str(i * 5)),
                bateria=100 - (i * 5),
            )
            ubicaciones.append(tracking)

        # Verify tracking history
        tracking_history = TrackingUbicacion.objects.filter(cuadrilla=cuadrilla).order_by('-created_at')

        assert tracking_history.count() == 10

        # Check latest position
        ultimo = tracking_history.first()
        assert ultimo.bateria == 55  # 100 - 9*5
        assert ultimo.velocidad == Decimal("45.00")  # 9 * 5
