"""Unit tests for campo app."""

import pytest
from datetime import timedelta
from decimal import Decimal
from django.utils import timezone

from apps.campo.models import RegistroCampo, Evidencia


@pytest.mark.django_db
class TestRegistroCampoModel:
    """Tests for RegistroCampo model."""

    def test_create_registro_campo(self):
        """Test creating a field record."""
        from tests.factories import RegistroCampoFactory

        registro = RegistroCampoFactory()
        assert registro.actividad is not None
        assert registro.usuario is not None
        assert registro.fecha_inicio is not None
        assert not registro.sincronizado

    def test_registro_campo_str(self):
        """Test field record string representation."""
        from tests.factories import RegistroCampoFactory

        registro = RegistroCampoFactory()
        str_repr = str(registro)
        assert "Registro" in str_repr

    def test_duracion_minutos_none_sin_fin(self):
        """Test duration is None when not finished."""
        from tests.factories import RegistroCampoFactory

        registro = RegistroCampoFactory(fecha_fin=None)
        assert registro.duracion_minutos is None

    def test_duracion_minutos_calculada(self):
        """Test duration calculation."""
        from tests.factories import RegistroCampoFactory

        inicio = timezone.now()
        fin = inicio + timedelta(hours=2, minutes=30)

        registro = RegistroCampoFactory(
            fecha_inicio=inicio,
            fecha_fin=fin,
        )
        assert registro.duracion_minutos == 150

    def test_total_evidencias(self):
        """Test evidence count property."""
        from tests.factories import (
            RegistroCampoFactory,
            EvidenciaAntesFactory,
            EvidenciaDuranteFactory,
            EvidenciaDespuesFactory,
        )

        registro = RegistroCampoFactory()
        EvidenciaAntesFactory(registro_campo=registro)
        EvidenciaDuranteFactory(registro_campo=registro)
        EvidenciaDespuesFactory(registro_campo=registro)

        assert registro.total_evidencias == 3

    def test_evidencias_completas_all_required(self):
        """Test evidence completeness check with all types required."""
        from tests.factories import (
            RegistroCampoFactory,
            EvidenciaAntesFactory,
            EvidenciaDuranteFactory,
            EvidenciaDespuesFactory,
            TipoActividadFactory,
            ActividadEnCursoFactory,
        )

        tipo = TipoActividadFactory(
            requiere_fotos_antes=True,
            requiere_fotos_durante=True,
            requiere_fotos_despues=True,
        )
        actividad = ActividadEnCursoFactory(tipo_actividad=tipo)
        registro = RegistroCampoFactory(actividad=actividad)

        # Initially incomplete
        assert not registro.evidencias_completas

        # Add all evidence types
        EvidenciaAntesFactory(registro_campo=registro)
        assert not registro.evidencias_completas

        EvidenciaDuranteFactory(registro_campo=registro)
        assert not registro.evidencias_completas

        EvidenciaDespuesFactory(registro_campo=registro)
        assert registro.evidencias_completas

    def test_evidencias_completas_partial_required(self):
        """Test evidence completeness when only some types are required."""
        from tests.factories import (
            RegistroCampoFactory,
            EvidenciaAntesFactory,
            TipoActividadFactory,
            ActividadEnCursoFactory,
        )

        tipo = TipoActividadFactory(
            requiere_fotos_antes=True,
            requiere_fotos_durante=False,
            requiere_fotos_despues=False,
        )
        actividad = ActividadEnCursoFactory(tipo_actividad=tipo)
        registro = RegistroCampoFactory(actividad=actividad)

        EvidenciaAntesFactory(registro_campo=registro)
        assert registro.evidencias_completas

    def test_datos_formulario_json(self):
        """Test form data JSON field."""
        from tests.factories import RegistroCampoFactory

        datos = {
            "observaciones": "Todo en orden",
            "metros_podados": 15.5,
            "estado_torre": "Bueno",
        }
        registro = RegistroCampoFactory(datos_formulario=datos)

        assert registro.datos_formulario["observaciones"] == "Todo en orden"
        assert registro.datos_formulario["metros_podados"] == 15.5

    def test_coordenadas_inicio(self):
        """Test start coordinates."""
        from tests.factories import RegistroCampoFactory

        registro = RegistroCampoFactory(
            latitud_inicio=Decimal("10.12345678"),
            longitud_inicio=Decimal("-74.87654321"),
        )
        assert registro.latitud_inicio == Decimal("10.12345678")
        assert registro.longitud_inicio == Decimal("-74.87654321")


@pytest.mark.django_db
class TestEvidenciaModel:
    """Tests for Evidencia model."""

    def test_create_evidencia(self):
        """Test creating evidence."""
        from tests.factories import EvidenciaFactory

        evidencia = EvidenciaFactory()
        assert evidencia.registro_campo is not None
        assert evidencia.tipo in ["ANTES", "DURANTE", "DESPUES"]
        assert evidencia.url_original

    def test_evidencia_str(self):
        """Test evidence string representation."""
        from tests.factories import EvidenciaAntesFactory

        evidencia = EvidenciaAntesFactory()
        str_repr = str(evidencia)
        assert "Antes" in str_repr

    def test_es_valida_true(self):
        """Test valid evidence detection."""
        from tests.factories import EvidenciaFactory

        evidencia = EvidenciaFactory(validacion_ia={"valida": True, "nitidez": 0.95})
        assert evidencia.es_valida

    def test_es_valida_false(self):
        """Test invalid evidence detection."""
        from tests.factories import EvidenciaFactory

        evidencia = EvidenciaFactory(validacion_ia={"valida": False, "nitidez": 0.3})
        assert not evidencia.es_valida

    def test_es_valida_default(self):
        """Test default validation when not set."""
        from tests.factories import EvidenciaFactory

        evidencia = EvidenciaFactory(validacion_ia={})
        assert evidencia.es_valida  # Default to True

    def test_puntaje_nitidez(self):
        """Test sharpness score property."""
        from tests.factories import EvidenciaFactory

        evidencia = EvidenciaFactory(validacion_ia={"nitidez": 0.87})
        assert evidencia.puntaje_nitidez == 0.87

    def test_puntaje_iluminacion(self):
        """Test lighting score property."""
        from tests.factories import EvidenciaFactory

        evidencia = EvidenciaFactory(validacion_ia={"iluminacion": 0.92})
        assert evidencia.puntaje_iluminacion == 0.92

    def test_tipos_evidencia(self):
        """Test all evidence types."""
        from tests.factories import (
            EvidenciaAntesFactory,
            EvidenciaDuranteFactory,
            EvidenciaDespuesFactory,
        )

        antes = EvidenciaAntesFactory()
        durante = EvidenciaDuranteFactory()
        despues = EvidenciaDespuesFactory()

        assert antes.tipo == "ANTES"
        assert durante.tipo == "DURANTE"
        assert despues.tipo == "DESPUES"

    def test_metadata_exif(self):
        """Test EXIF metadata storage."""
        from tests.factories import EvidenciaFactory

        metadata = {
            "make": "Samsung",
            "model": "Galaxy S23",
            "datetime": "2025-01-15 10:30:00",
            "gps": True,
            "latitude": 10.12345,
            "longitude": -74.87654,
        }
        evidencia = EvidenciaFactory(metadata_exif=metadata)

        assert evidencia.metadata_exif["make"] == "Samsung"
        assert evidencia.metadata_exif["gps"] is True


@pytest.mark.django_db
class TestCampoFactories:
    """Tests for campo factories."""

    def test_registro_campo_factory(self):
        """Test RegistroCampoFactory."""
        from tests.factories import RegistroCampoFactory

        registro = RegistroCampoFactory()
        assert registro.actividad
        assert registro.usuario
        assert registro.fecha_inicio
        assert not registro.sincronizado

    def test_registro_campo_completado_factory(self):
        """Test RegistroCampoCompletadoFactory."""
        from tests.factories import RegistroCampoCompletadoFactory

        registro = RegistroCampoCompletadoFactory()
        assert registro.fecha_fin
        assert registro.latitud_fin
        assert registro.longitud_fin
        assert registro.sincronizado

    def test_evidencia_factory(self):
        """Test EvidenciaFactory."""
        from tests.factories import EvidenciaFactory

        evidencia = EvidenciaFactory()
        assert evidencia.registro_campo
        assert evidencia.url_original
        assert evidencia.fecha_captura
