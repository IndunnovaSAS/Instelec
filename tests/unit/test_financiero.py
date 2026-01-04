"""Unit tests for financiero app."""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from apps.financiero.models import CostoRecurso, Presupuesto, EjecucionCosto, CicloFacturacion


@pytest.mark.django_db
class TestCostoRecursoModel:
    """Tests for CostoRecurso model."""

    def test_create_costo_recurso(self):
        """Test creating a resource cost."""
        costo = CostoRecurso.objects.create(
            tipo=CostoRecurso.TipoRecurso.DIA_HOMBRE,
            descripcion="Día hombre liniero",
            costo_unitario=Decimal("120000.00"),
            unidad="DIA",
            vigencia_desde=date.today() - timedelta(days=365),
        )
        assert costo.tipo == "DIA_HOMBRE"
        assert costo.costo_unitario == Decimal("120000.00")
        assert costo.activo

    def test_costo_recurso_str(self):
        """Test resource cost string representation."""
        costo = CostoRecurso.objects.create(
            tipo=CostoRecurso.TipoRecurso.VEHICULO,
            descripcion="Camioneta 4x4",
            costo_unitario=Decimal("180000.00"),
            unidad="DIA",
            vigencia_desde=date.today(),
        )
        str_repr = str(costo)
        assert "Vehículo" in str_repr
        assert "Camioneta 4x4" in str_repr

    def test_tipos_recurso(self):
        """Test all resource types."""
        tipos = [
            CostoRecurso.TipoRecurso.DIA_HOMBRE,
            CostoRecurso.TipoRecurso.VEHICULO,
            CostoRecurso.TipoRecurso.VIATICO,
            CostoRecurso.TipoRecurso.HERRAMIENTA,
            CostoRecurso.TipoRecurso.MATERIAL,
            CostoRecurso.TipoRecurso.OTRO,
        ]
        for i, tipo in enumerate(tipos):
            costo = CostoRecurso.objects.create(
                tipo=tipo,
                descripcion=f"Recurso tipo {i}",
                costo_unitario=Decimal("100000.00"),
                unidad="UNIDAD",
                vigencia_desde=date.today(),
            )
            assert costo.tipo == tipo


@pytest.mark.django_db
class TestPresupuestoModel:
    """Tests for Presupuesto model."""

    def test_create_presupuesto(self):
        """Test creating a budget."""
        from tests.factories import PresupuestoFactory

        presupuesto = PresupuestoFactory()
        assert presupuesto.anio
        assert presupuesto.mes
        assert presupuesto.linea
        assert presupuesto.estado == Presupuesto.Estado.PROYECTADO

    def test_presupuesto_str(self):
        """Test budget string representation."""
        from tests.factories import PresupuestoFactory, LineaFactory

        linea = LineaFactory(codigo="LT-FIN-001")
        presupuesto = PresupuestoFactory(
            linea=linea,
            mes=6,
            anio=2025,
        )
        str_repr = str(presupuesto)
        assert "LT-FIN-001" in str_repr
        assert "6/2025" in str_repr

    def test_presupuesto_estados(self):
        """Test all budget states."""
        from tests.factories import PresupuestoFactory

        estados = [
            Presupuesto.Estado.PROYECTADO,
            Presupuesto.Estado.APROBADO,
            Presupuesto.Estado.EN_EJECUCION,
            Presupuesto.Estado.CERRADO,
        ]
        for estado in estados:
            presupuesto = PresupuestoFactory(estado=estado)
            assert presupuesto.estado == estado

    def test_presupuesto_unique_together(self):
        """Test that anio, mes, linea must be unique together."""
        from tests.factories import PresupuestoFactory, LineaFactory

        linea = LineaFactory()
        PresupuestoFactory(
            linea=linea,
            mes=6,
            anio=2025,
        )
        with pytest.raises(Exception):
            PresupuestoFactory(
                linea=linea,
                mes=6,
                anio=2025,
            )

    def test_presupuesto_desviacion_positiva(self):
        """Test positive budget deviation (over budget)."""
        from tests.factories import PresupuestoFactory

        presupuesto = PresupuestoFactory(
            total_presupuestado=Decimal("10000000.00"),
            total_ejecutado=Decimal("12000000.00"),
        )
        assert presupuesto.desviacion == 20  # 20% over budget

    def test_presupuesto_desviacion_negativa(self):
        """Test negative budget deviation (under budget)."""
        from tests.factories import PresupuestoFactory

        presupuesto = PresupuestoFactory(
            total_presupuestado=Decimal("10000000.00"),
            total_ejecutado=Decimal("8000000.00"),
        )
        assert presupuesto.desviacion == -20  # 20% under budget

    def test_presupuesto_desviacion_cero_division(self):
        """Test deviation when presupuesto is zero."""
        from tests.factories import PresupuestoFactory

        presupuesto = PresupuestoFactory(
            total_presupuestado=Decimal("0.00"),
            total_ejecutado=Decimal("1000000.00"),
        )
        assert presupuesto.desviacion == 0

    def test_presupuesto_utilidad_proyectada(self):
        """Test projected profit calculation."""
        from tests.factories import PresupuestoFactory

        presupuesto = PresupuestoFactory(
            total_presupuestado=Decimal("10000000.00"),
            facturacion_esperada=Decimal("12000000.00"),
        )
        assert presupuesto.utilidad_proyectada == Decimal("2000000.00")

    def test_presupuesto_calcular_totales(self):
        """Test total calculation method."""
        from tests.factories import PresupuestoFactory

        presupuesto = PresupuestoFactory(
            costo_dias_hombre=Decimal("5000000.00"),
            costo_vehiculos=Decimal("2000000.00"),
            viaticos_planeados=Decimal("1500000.00"),
            otros_costos=Decimal("500000.00"),
            total_presupuestado=Decimal("0.00"),
        )
        presupuesto.calcular_totales()
        presupuesto.refresh_from_db()

        assert presupuesto.total_presupuestado == Decimal("9000000.00")


@pytest.mark.django_db
class TestEjecucionCostoModel:
    """Tests for EjecucionCosto model."""

    def test_create_ejecucion_costo(self):
        """Test creating a cost execution."""
        from tests.factories import EjecucionCostoFactory

        ejecucion = EjecucionCostoFactory()
        assert ejecucion.presupuesto
        assert ejecucion.concepto
        assert ejecucion.tipo_recurso
        assert ejecucion.cantidad
        assert ejecucion.costo_unitario
        assert ejecucion.costo_total

    def test_ejecucion_costo_str(self):
        """Test cost execution string representation."""
        from tests.factories import EjecucionCostoFactory

        ejecucion = EjecucionCostoFactory(
            concepto="Días hombre liniero",
            fecha=date(2025, 6, 15),
        )
        str_repr = str(ejecucion)
        assert "Días hombre liniero" in str_repr

    def test_ejecucion_costo_total_calculado(self):
        """Test that costo_total is calculated on save."""
        from tests.factories import PresupuestoEnEjecucionFactory

        presupuesto = PresupuestoEnEjecucionFactory()
        ejecucion = EjecucionCosto.objects.create(
            presupuesto=presupuesto,
            concepto="Días hombre",
            tipo_recurso=CostoRecurso.TipoRecurso.DIA_HOMBRE,
            cantidad=Decimal("5.00"),
            costo_unitario=Decimal("120000.00"),
            costo_total=Decimal("0.00"),  # Will be recalculated
            fecha=date.today(),
        )
        assert ejecucion.costo_total == Decimal("600000.00")


@pytest.mark.django_db
class TestCicloFacturacionModel:
    """Tests for CicloFacturacion model."""

    def test_create_ciclo_facturacion(self):
        """Test creating a billing cycle."""
        from tests.factories import CicloFacturacionFactory

        ciclo = CicloFacturacionFactory()
        assert ciclo.presupuesto
        assert ciclo.estado == CicloFacturacion.Estado.INFORME_GENERADO

    def test_ciclo_facturacion_str(self):
        """Test billing cycle string representation."""
        from tests.factories import CicloFacturacionFactory

        ciclo = CicloFacturacionFactory()
        str_repr = str(ciclo)
        assert "Facturación" in str_repr

    def test_ciclo_estados(self):
        """Test all billing cycle states."""
        from tests.factories import CicloFacturacionFactory

        estados = [
            CicloFacturacion.Estado.INFORME_GENERADO,
            CicloFacturacion.Estado.EN_VALIDACION,
            CicloFacturacion.Estado.ORDEN_ENTREGA,
            CicloFacturacion.Estado.FACTURA_EMITIDA,
            CicloFacturacion.Estado.PAGO_RECIBIDO,
        ]
        for estado in estados:
            ciclo = CicloFacturacionFactory(estado=estado)
            assert ciclo.estado == estado

    def test_ciclo_dias_ciclo_completo(self):
        """Test cycle days calculation."""
        from tests.factories import CicloFacturacionFactory

        ciclo = CicloFacturacionFactory(
            fecha_informe=date(2025, 1, 1),
            fecha_pago=date(2025, 2, 15),
        )
        assert ciclo.dias_ciclo == 45

    def test_ciclo_dias_ciclo_sin_pago(self):
        """Test cycle days when payment not received."""
        from tests.factories import CicloFacturacionFactory

        ciclo = CicloFacturacionFactory(
            fecha_informe=date.today(),
            fecha_pago=None,
        )
        assert ciclo.dias_ciclo is None

    def test_ciclo_datos_facturacion(self):
        """Test billing data."""
        from tests.factories import CicloFacturacionPagadoFactory

        ciclo = CicloFacturacionPagadoFactory(
            numero_factura="FE-1234",
            numero_orden="OE-5678",
        )
        assert ciclo.numero_factura == "FE-1234"
        assert ciclo.numero_orden == "OE-5678"
        assert ciclo.monto_facturado > 0
        assert ciclo.monto_pagado > 0


@pytest.mark.django_db
class TestFinancieroFactories:
    """Tests for financiero factories."""

    def test_costo_recurso_factory(self):
        """Test CostoRecursoFactory."""
        from tests.factories import CostoRecursoFactory

        costo = CostoRecursoFactory()
        assert costo.tipo
        assert costo.descripcion
        assert costo.costo_unitario

    def test_presupuesto_factory(self):
        """Test PresupuestoFactory."""
        from tests.factories import PresupuestoFactory

        presupuesto = PresupuestoFactory()
        assert presupuesto.linea
        assert presupuesto.anio
        assert presupuesto.mes

    def test_presupuesto_en_ejecucion_factory(self):
        """Test PresupuestoEnEjecucionFactory."""
        from tests.factories import PresupuestoEnEjecucionFactory

        presupuesto = PresupuestoEnEjecucionFactory()
        assert presupuesto.estado == Presupuesto.Estado.EN_EJECUCION
        assert presupuesto.total_ejecutado > 0

    def test_ejecucion_costo_factory(self):
        """Test EjecucionCostoFactory."""
        from tests.factories import EjecucionCostoFactory

        ejecucion = EjecucionCostoFactory()
        assert ejecucion.presupuesto
        assert ejecucion.costo_total > 0

    def test_ciclo_facturacion_pagado_factory(self):
        """Test CicloFacturacionPagadoFactory."""
        from tests.factories import CicloFacturacionPagadoFactory

        ciclo = CicloFacturacionPagadoFactory()
        assert ciclo.estado == CicloFacturacion.Estado.PAGO_RECIBIDO
        assert ciclo.fecha_pago
        assert ciclo.monto_pagado > 0
