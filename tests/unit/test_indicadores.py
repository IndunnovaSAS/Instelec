"""Unit tests for indicadores app."""

import pytest
from datetime import date, timedelta
from decimal import Decimal

from apps.indicadores.models import Indicador, MedicionIndicador, ActaSeguimiento


@pytest.mark.django_db
class TestIndicadorModel:
    """Tests for Indicador model."""

    def test_create_indicador(self):
        """Test creating an indicator."""
        indicador = Indicador.objects.create(
            codigo="IND-001",
            nombre="Gestión de Mantenimiento",
            categoria=Indicador.Categoria.GESTION,
            formula="(Actividades Ejecutadas / Actividades Programadas) * 100",
            meta=Decimal("95.00"),
            umbral_alerta=Decimal("85.00"),
        )
        assert indicador.codigo == "IND-001"
        assert indicador.meta == Decimal("95.00")
        assert indicador.activo

    def test_indicador_str(self):
        """Test indicator string representation."""
        indicador = Indicador.objects.create(
            codigo="IND-STR",
            nombre="Indicador de prueba",
            categoria=Indicador.Categoria.CALIDAD,
            formula="Formula de prueba",
            meta=Decimal("90.00"),
            umbral_alerta=Decimal("80.00"),
        )
        str_repr = str(indicador)
        assert "IND-STR" in str_repr
        assert "Indicador de prueba" in str_repr

    def test_indicador_unique_codigo(self):
        """Test that codigo is unique."""
        Indicador.objects.create(
            codigo="UNIQUE-IND",
            nombre="Primer indicador",
            categoria=Indicador.Categoria.GESTION,
            formula="Formula",
            meta=Decimal("90.00"),
            umbral_alerta=Decimal("80.00"),
        )
        with pytest.raises(Exception):
            Indicador.objects.create(
                codigo="UNIQUE-IND",
                nombre="Segundo indicador",
                categoria=Indicador.Categoria.EJECUCION,
                formula="Otra formula",
                meta=Decimal("85.00"),
                umbral_alerta=Decimal("75.00"),
            )

    def test_categorias_indicador(self):
        """Test all indicator categories."""
        categorias = [
            Indicador.Categoria.GESTION,
            Indicador.Categoria.EJECUCION,
            Indicador.Categoria.AMBIENTAL,
            Indicador.Categoria.SEGURIDAD,
            Indicador.Categoria.CALIDAD,
        ]
        for i, cat in enumerate(categorias):
            indicador = Indicador.objects.create(
                codigo=f"CAT-{i:03d}",
                nombre=f"Indicador {cat}",
                categoria=cat,
                formula="Formula",
                meta=Decimal("90.00"),
                umbral_alerta=Decimal("80.00"),
            )
            assert indicador.categoria == cat


@pytest.mark.django_db
class TestMedicionIndicadorModel:
    """Tests for MedicionIndicador model."""

    def test_create_medicion(self):
        """Test creating a measurement."""
        from tests.factories import MedicionIndicadorFactory

        medicion = MedicionIndicadorFactory()
        assert medicion.indicador
        assert medicion.linea
        assert medicion.anio
        assert medicion.mes

    def test_medicion_str(self):
        """Test measurement string representation."""
        from tests.factories import MedicionIndicadorFactory, IndicadorFactory

        indicador = IndicadorFactory(codigo="MED-STR")
        medicion = MedicionIndicadorFactory(
            indicador=indicador,
            mes=6,
            anio=2025,
            valor_calculado=Decimal("92.50"),
        )
        str_repr = str(medicion)
        assert "MED-STR" in str_repr
        assert "6/2025" in str_repr

    def test_medicion_unique_together(self):
        """Test that indicador, linea, anio, mes must be unique together."""
        from tests.factories import MedicionIndicadorFactory, IndicadorFactory, LineaFactory

        indicador = IndicadorFactory()
        linea = LineaFactory()
        MedicionIndicadorFactory(
            indicador=indicador,
            linea=linea,
            anio=2025,
            mes=6,
        )
        with pytest.raises(Exception):
            MedicionIndicadorFactory(
                indicador=indicador,
                linea=linea,
                anio=2025,
                mes=6,
            )

    def test_medicion_calcular_cumple_meta(self):
        """Test calculation meeting target."""
        from tests.factories import IndicadorFactory, LineaFactory

        indicador = IndicadorFactory(meta=Decimal("90.00"), umbral_alerta=Decimal("80.00"))
        linea = LineaFactory()

        medicion = MedicionIndicador.objects.create(
            indicador=indicador,
            linea=linea,
            anio=2025,
            mes=6,
            valor_numerador=Decimal("95.00"),
            valor_denominador=Decimal("100.00"),
        )
        medicion.calcular()

        assert medicion.valor_calculado == Decimal("95.00")
        assert medicion.cumple_meta
        assert not medicion.en_alerta

    def test_medicion_calcular_en_alerta(self):
        """Test calculation in alert state."""
        from tests.factories import IndicadorFactory, LineaFactory

        indicador = IndicadorFactory(meta=Decimal("90.00"), umbral_alerta=Decimal("80.00"))
        linea = LineaFactory()

        medicion = MedicionIndicador.objects.create(
            indicador=indicador,
            linea=linea,
            anio=2025,
            mes=6,
            valor_numerador=Decimal("75.00"),
            valor_denominador=Decimal("100.00"),
        )
        medicion.calcular()

        assert medicion.valor_calculado == Decimal("75.00")
        assert not medicion.cumple_meta
        assert medicion.en_alerta

    def test_medicion_calcular_denominador_cero(self):
        """Test calculation with zero denominator."""
        from tests.factories import IndicadorFactory, LineaFactory

        indicador = IndicadorFactory(meta=Decimal("90.00"), umbral_alerta=Decimal("80.00"))
        linea = LineaFactory()

        medicion = MedicionIndicador.objects.create(
            indicador=indicador,
            linea=linea,
            anio=2025,
            mes=6,
            valor_numerador=Decimal("50.00"),
            valor_denominador=Decimal("0.00"),
            valor_calculado=Decimal("50.00"),
        )
        medicion.calcular()

        # Value should not be recalculated when denominator is 0
        assert medicion.valor_calculado == Decimal("50.00")


@pytest.mark.django_db
class TestActaSeguimientoModel:
    """Tests for ActaSeguimiento model."""

    def test_create_acta(self):
        """Test creating meeting minutes."""
        from tests.factories import ActaSeguimientoFactory

        acta = ActaSeguimientoFactory()
        assert acta.linea
        assert acta.anio
        assert acta.mes
        assert acta.fecha_reunion
        assert acta.estado == ActaSeguimiento.Estado.BORRADOR

    def test_acta_str(self):
        """Test meeting minutes string representation."""
        from tests.factories import ActaSeguimientoFactory, LineaFactory

        linea = LineaFactory(codigo="LT-ACTA-001")
        acta = ActaSeguimientoFactory(
            linea=linea,
            mes=6,
            anio=2025,
        )
        str_repr = str(acta)
        assert "LT-ACTA-001" in str_repr
        assert "6/2025" in str_repr

    def test_acta_unique_together(self):
        """Test that linea, anio, mes must be unique together."""
        from tests.factories import ActaSeguimientoFactory, LineaFactory

        linea = LineaFactory()
        ActaSeguimientoFactory(
            linea=linea,
            anio=2025,
            mes=6,
        )
        with pytest.raises(Exception):
            ActaSeguimientoFactory(
                linea=linea,
                anio=2025,
                mes=6,
            )

    def test_acta_estados(self):
        """Test all meeting minutes states."""
        from tests.factories import ActaSeguimientoFactory

        estados = [
            ActaSeguimiento.Estado.BORRADOR,
            ActaSeguimiento.Estado.PENDIENTE_FIRMA,
            ActaSeguimiento.Estado.FIRMADA,
        ]
        for estado in estados:
            acta = ActaSeguimientoFactory(estado=estado)
            assert acta.estado == estado

    def test_acta_resumen_indicadores_json(self):
        """Test indicator summary JSON field."""
        from tests.factories import ActaSeguimientoFactory

        resumen = {
            "gestion": 95.5,
            "ejecucion": 92.0,
            "ambiental": 98.0,
            "seguridad": 100.0,
            "calidad": 94.5,
            "indice_global": 95.2,
        }
        acta = ActaSeguimientoFactory(resumen_indicadores=resumen)

        assert acta.resumen_indicadores["gestion"] == 95.5
        assert acta.resumen_indicadores["indice_global"] == 95.2

    def test_acta_asistentes(self):
        """Test attendees fields."""
        from tests.factories import ActaSeguimientoFactory

        acta = ActaSeguimientoFactory(
            asistentes_instelec="Juan Pérez, María García",
            asistentes_cliente="Carlos López, Ana Martínez",
        )
        assert "Juan Pérez" in acta.asistentes_instelec
        assert "Carlos López" in acta.asistentes_cliente


@pytest.mark.django_db
class TestIndicadoresFactories:
    """Tests for indicadores factories."""

    def test_indicador_factory(self):
        """Test IndicadorFactory."""
        from tests.factories import IndicadorFactory

        indicador = IndicadorFactory()
        assert indicador.codigo
        assert indicador.nombre
        assert indicador.meta
        assert indicador.umbral_alerta

    def test_indicador_gestion_factory(self):
        """Test IndicadorGestionFactory."""
        from tests.factories import IndicadorGestionFactory

        indicador = IndicadorGestionFactory()
        assert indicador.categoria == Indicador.Categoria.GESTION

    def test_indicador_seguridad_factory(self):
        """Test IndicadorSeguridadFactory."""
        from tests.factories import IndicadorSeguridadFactory

        indicador = IndicadorSeguridadFactory()
        assert indicador.categoria == Indicador.Categoria.SEGURIDAD
        assert indicador.meta == Decimal("100.00")

    def test_medicion_cumple_meta_factory(self):
        """Test MedicionCumpleMeta."""
        from tests.factories import MedicionCumpleMeta

        medicion = MedicionCumpleMeta()
        assert medicion.valor_numerador == Decimal("98.00")

    def test_medicion_en_alerta_factory(self):
        """Test MedicionEnAlerta."""
        from tests.factories import MedicionEnAlerta

        medicion = MedicionEnAlerta()
        assert medicion.valor_numerador == Decimal("75.00")

    def test_acta_seguimiento_factory(self):
        """Test ActaSeguimientoFactory."""
        from tests.factories import ActaSeguimientoFactory

        acta = ActaSeguimientoFactory()
        assert acta.linea
        assert acta.fecha_reunion
        assert acta.estado == ActaSeguimiento.Estado.BORRADOR

    def test_acta_seguimiento_firmada_factory(self):
        """Test ActaSeguimientoFirmadaFactory."""
        from tests.factories import ActaSeguimientoFirmadaFactory

        acta = ActaSeguimientoFirmadaFactory()
        assert acta.estado == ActaSeguimiento.Estado.FIRMADA
        assert acta.url_acta_firmada
