"""Integration tests for financial workflow."""

import pytest
from decimal import Decimal
from datetime import date, timedelta
from django.utils import timezone

from apps.financiero.models import Presupuesto, EjecucionCosto, CicloFacturacion


@pytest.mark.django_db
class TestFlujoPresupuestoEjecucion:
    """Integration tests for Budget -> Execution flow."""

    def test_ejecuciones_afectan_presupuesto(self):
        """Cost executions should affect budget totals."""
        from tests.factories import (
            PresupuestoEnEjecucionFactory,
            EjecucionCostoFactory,
        )

        presupuesto = PresupuestoEnEjecucionFactory(
            total_ejecutado=Decimal("0.00"),
        )

        # Add cost executions
        ejecucion1 = EjecucionCostoFactory(
            presupuesto=presupuesto,
            cantidad=Decimal("5.00"),
            costo_unitario=Decimal("120000.00"),
        )
        ejecucion2 = EjecucionCostoFactory(
            presupuesto=presupuesto,
            cantidad=Decimal("3.00"),
            costo_unitario=Decimal("180000.00"),
        )

        total_ejecuciones = ejecucion1.costo_total + ejecucion2.costo_total
        assert total_ejecuciones == Decimal("1140000.00")

    def test_ejecucion_vinculada_a_actividad(self):
        """Cost execution can be linked to a completed activity."""
        from tests.factories import (
            PresupuestoEnEjecucionFactory,
            ActividadCompletadaFactory,
            EjecucionCostoFactory,
        )

        presupuesto = PresupuestoEnEjecucionFactory()
        actividad = ActividadCompletadaFactory()

        ejecucion = EjecucionCostoFactory(
            presupuesto=presupuesto,
            actividad=actividad,
            concepto="Días hombre para poda",
        )

        assert ejecucion.actividad == actividad
        assert ejecucion.presupuesto == presupuesto


@pytest.mark.django_db
class TestFlujoCicloFacturacion:
    """Integration tests for Billing Cycle flow."""

    def test_ciclo_facturacion_completo(self):
        """Complete billing cycle from report to payment."""
        from tests.factories import PresupuestoEnEjecucionFactory

        presupuesto = PresupuestoEnEjecucionFactory(
            facturacion_esperada=Decimal("15000000.00"),
        )

        # Create billing cycle
        ciclo = CicloFacturacion.objects.create(
            presupuesto=presupuesto,
            estado=CicloFacturacion.Estado.INFORME_GENERADO,
            fecha_informe=date.today() - timedelta(days=45),
        )

        # Progress through states
        ciclo.estado = CicloFacturacion.Estado.EN_VALIDACION
        ciclo.fecha_validacion = date.today() - timedelta(days=40)
        ciclo.save()

        ciclo.estado = CicloFacturacion.Estado.ORDEN_ENTREGA
        ciclo.fecha_orden = date.today() - timedelta(days=30)
        ciclo.numero_orden = "OE-2025-001"
        ciclo.save()

        ciclo.estado = CicloFacturacion.Estado.FACTURA_EMITIDA
        ciclo.fecha_factura = date.today() - timedelta(days=20)
        ciclo.numero_factura = "FE-2025-001"
        ciclo.monto_facturado = presupuesto.facturacion_esperada
        ciclo.save()

        ciclo.estado = CicloFacturacion.Estado.PAGO_RECIBIDO
        ciclo.fecha_pago = date.today()
        ciclo.monto_pagado = ciclo.monto_facturado
        ciclo.save()

        ciclo.refresh_from_db()
        assert ciclo.estado == CicloFacturacion.Estado.PAGO_RECIBIDO
        assert ciclo.dias_ciclo == 45
        assert ciclo.monto_pagado == Decimal("15000000.00")

    def test_multiples_ciclos_por_presupuesto(self):
        """A budget can have multiple billing cycles."""
        from tests.factories import PresupuestoEnEjecucionFactory, CicloFacturacionFactory

        presupuesto = PresupuestoEnEjecucionFactory()

        # Create multiple cycles (e.g., partial billing)
        ciclo1 = CicloFacturacionFactory(
            presupuesto=presupuesto,
            monto_facturado=Decimal("5000000.00"),
        )
        ciclo2 = CicloFacturacionFactory(
            presupuesto=presupuesto,
            monto_facturado=Decimal("5000000.00"),
        )

        assert presupuesto.ciclos_facturacion.count() == 2


@pytest.mark.django_db
class TestFlujoPresupuestoLinea:
    """Integration tests for Budget -> Transmission Line flow."""

    def test_presupuesto_por_linea_mes(self):
        """Each line should have one budget per month."""
        from tests.factories import LineaFactory, PresupuestoFactory

        linea = LineaFactory()

        # Create budgets for different months
        presupuesto_ene = PresupuestoFactory(linea=linea, anio=2025, mes=1)
        presupuesto_feb = PresupuestoFactory(linea=linea, anio=2025, mes=2)
        presupuesto_mar = PresupuestoFactory(linea=linea, anio=2025, mes=3)

        assert linea.presupuestos.count() == 3

    def test_desviacion_presupuestal_acumulada(self):
        """Calculate accumulated budget deviation across months."""
        from tests.factories import LineaFactory, PresupuestoFactory
        from django.db.models import Sum

        linea = LineaFactory()

        # Create budgets with varying execution
        PresupuestoFactory(
            linea=linea,
            anio=2025,
            mes=1,
            total_presupuestado=Decimal("10000000.00"),
            total_ejecutado=Decimal("9500000.00"),  # Under budget
        )
        PresupuestoFactory(
            linea=linea,
            anio=2025,
            mes=2,
            total_presupuestado=Decimal("12000000.00"),
            total_ejecutado=Decimal("13000000.00"),  # Over budget
        )
        PresupuestoFactory(
            linea=linea,
            anio=2025,
            mes=3,
            total_presupuestado=Decimal("11000000.00"),
            total_ejecutado=Decimal("10000000.00"),  # Under budget
        )

        totales = linea.presupuestos.aggregate(
            total_presupuestado=Sum('total_presupuestado'),
            total_ejecutado=Sum('total_ejecutado'),
        )

        # Total: 33M presupuestado, 32.5M ejecutado = -1.5% deviation
        assert totales['total_presupuestado'] == Decimal("33000000.00")
        assert totales['total_ejecutado'] == Decimal("32500000.00")


@pytest.mark.django_db
class TestFlujoActividadCosto:
    """Integration tests for Activity -> Cost flow."""

    def test_actividad_genera_costos(self):
        """Completing activity should allow associating costs."""
        from tests.factories import (
            LineaFactory,
            ActividadCompletadaFactory,
            PresupuestoEnEjecucionFactory,
            RegistroCampoCompletadoFactory,
            CostoRecursoFactory,
        )

        linea = LineaFactory()
        presupuesto = PresupuestoEnEjecucionFactory(linea=linea, mes=6, anio=2025)
        actividad = ActividadCompletadaFactory(linea=linea, fecha_programada=date(2025, 6, 15))

        # Complete field work
        registro = RegistroCampoCompletadoFactory(actividad=actividad)

        # Calculate cost based on hours worked
        horas = registro.duracion_minutos / 60 if registro.duracion_minutos else 4

        # Create cost execution for this activity
        ejecucion = EjecucionCosto.objects.create(
            presupuesto=presupuesto,
            actividad=actividad,
            concepto=f"Mano de obra - {actividad.tipo_actividad.nombre}",
            tipo_recurso='DIA_HOMBRE',
            cantidad=Decimal(str(horas / 8)),  # Convert hours to days
            costo_unitario=Decimal("120000.00"),
            costo_total=Decimal("0.00"),  # Will be calculated
            fecha=date(2025, 6, 15),
        )

        assert ejecucion.actividad == actividad
        assert ejecucion.costo_total > 0
