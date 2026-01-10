"""Unit tests for photo validators."""

import io
import pytest
from datetime import datetime
from PIL import Image

from apps.campo.validators import (
    PhotoValidator,
    ValidationResult,
    validate_evidence_photo,
    validate_photo_set,
)


def create_test_image(
    width: int = 1280,
    height: int = 720,
    color: tuple = (128, 128, 128),
    format: str = 'JPEG',
    add_noise: bool = True
) -> bytes:
    """Create a test image with specified dimensions.

    Args:
        width: Image width
        height: Image height
        color: Base RGB color tuple
        format: Image format (JPEG, PNG, etc.)
        add_noise: If True, adds noise for contrast/sharpness (needed to pass validation)
    """
    import numpy as np

    if add_noise and color not in [(10, 10, 10), (250, 250, 250)]:
        # Create image with noise for contrast and sharpness
        np.random.seed(42)  # Reproducible results
        noise = np.random.randint(-50, 51, (height, width, 3), dtype=np.int16)
        base = np.array(color, dtype=np.int16)
        img_array = base + noise
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        img = Image.fromarray(img_array, 'RGB')
    else:
        img = Image.new('RGB', (width, height), color)

    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    return buffer.getvalue()


class TestPhotoValidator:
    """Tests for PhotoValidator class."""

    def test_valid_image_passes(self):
        """A valid image should pass validation."""
        image_bytes = create_test_image(1280, 720)
        validator = PhotoValidator(image_bytes)
        result = validator.validate()

        assert result.is_valid is True
        assert result.score >= 0.6
        assert len(result.errors) == 0

    def test_invalid_format_fails(self):
        """Invalid image format should fail."""
        # Create invalid bytes
        invalid_bytes = b"not an image"
        validator = PhotoValidator(invalid_bytes)
        result = validator.validate()

        assert result.is_valid is False
        assert 'Cannot open image' in result.errors[0]

    def test_low_resolution_fails(self):
        """Image with resolution below minimum should fail."""
        image_bytes = create_test_image(320, 240)  # Too small
        validator = PhotoValidator(image_bytes)
        result = validator.validate()

        assert result.is_valid is False
        assert any('Resolution too low' in e for e in result.errors)

    def test_dark_image_fails(self):
        """Very dark image should fail."""
        image_bytes = create_test_image(1280, 720, color=(10, 10, 10), add_noise=False)
        validator = PhotoValidator(image_bytes)
        result = validator.validate()

        assert result.is_valid is False
        assert any('too dark' in e or 'blurry' in e for e in result.errors)

    def test_overexposed_image_fails(self):
        """Overexposed image should fail."""
        image_bytes = create_test_image(1280, 720, color=(250, 250, 250), add_noise=False)
        validator = PhotoValidator(image_bytes)
        result = validator.validate()

        assert result.is_valid is False
        assert any('overexposed' in e or 'blurry' in e for e in result.errors)

    def test_medium_resolution_warning(self):
        """Medium resolution should trigger warning but pass."""
        image_bytes = create_test_image(800, 600)  # Valid but low
        validator = PhotoValidator(image_bytes)
        result = validator.validate()

        # Should pass but have warning
        assert any('Low resolution' in w for w in result.warnings)

    def test_gps_validation_too_far(self):
        """GPS location too far from expected should fail."""
        image_bytes = create_test_image(1280, 720)
        validator = PhotoValidator(image_bytes)

        # Set up mock metadata
        validator.image = Image.open(io.BytesIO(image_bytes))
        validator.metadata = {
            'latitude': 4.7110,  # Bogotá
            'longitude': -74.0721
        }

        # Expected location in Medellín (far away)
        score = validator._validate_gps(6.2442, -75.5812)

        assert score == 0.0
        assert any('Location too far' in e for e in validator.errors)

    def test_gps_validation_close(self):
        """GPS location close to expected should pass."""
        image_bytes = create_test_image(1280, 720)
        validator = PhotoValidator(image_bytes)

        validator.image = Image.open(io.BytesIO(image_bytes))
        validator.metadata = {
            'latitude': 4.7110,
            'longitude': -74.0721
        }

        # Expected location very close
        score = validator._validate_gps(4.7115, -74.0725)

        assert score == 1.0
        assert len(validator.errors) == 0


class TestValidateEvidencePhoto:
    """Tests for validate_evidence_photo function."""

    def test_returns_dict_with_expected_keys(self):
        """Should return dictionary with all expected keys."""
        image_bytes = create_test_image(1280, 720)
        result = validate_evidence_photo(image_bytes)

        assert 'valid' in result
        assert 'score' in result
        assert 'errors' in result
        assert 'warnings' in result
        assert 'metadata' in result
        assert 'message' in result

    def test_valid_image_returns_valid_true(self):
        """Valid image should return valid=True."""
        image_bytes = create_test_image(1280, 720)
        result = validate_evidence_photo(image_bytes)

        assert result['valid'] is True
        assert result['message'] == 'Photo is valid'

    def test_invalid_image_returns_valid_false(self):
        """Invalid image should return valid=False."""
        result = validate_evidence_photo(b"invalid")

        assert result['valid'] is False
        assert result['message'] != 'Photo is valid'


class TestValidatePhotoSet:
    """Tests for validate_photo_set function."""

    def test_complete_set_passes(self):
        """Complete set of valid photos should pass."""
        photos = [
            {'type': 'ANTES', 'bytes': create_test_image(1280, 720)},
            {'type': 'DURANTE', 'bytes': create_test_image(1280, 720)},
            {'type': 'DESPUES', 'bytes': create_test_image(1280, 720)},
        ]

        result = validate_photo_set(photos)

        assert result['all_valid'] is True
        assert len(result['missing_types']) == 0
        assert result['message'] == 'All photos valid'

    def test_missing_type_fails(self):
        """Missing photo type should fail."""
        photos = [
            {'type': 'ANTES', 'bytes': create_test_image(1280, 720)},
            {'type': 'DURANTE', 'bytes': create_test_image(1280, 720)},
            # Missing DESPUES
        ]

        result = validate_photo_set(photos)

        assert result['all_valid'] is False
        assert 'DESPUES' in result['missing_types']
        assert 'Missing photo types' in result['message']

    def test_invalid_photo_fails(self):
        """Set with invalid photo should fail."""
        photos = [
            {'type': 'ANTES', 'bytes': create_test_image(1280, 720)},
            {'type': 'DURANTE', 'bytes': b"invalid"},  # Invalid
            {'type': 'DESPUES', 'bytes': create_test_image(1280, 720)},
        ]

        result = validate_photo_set(photos)

        assert result['all_valid'] is False
        assert result['results']['DURANTE']['valid'] is False

    def test_empty_set_fails(self):
        """Empty photo set should fail."""
        result = validate_photo_set([])

        assert result['all_valid'] is False
        assert len(result['missing_types']) == 3


class TestHaversineDistance:
    """Tests for distance calculation."""

    def test_same_point_zero_distance(self):
        """Same point should have zero distance."""
        validator = PhotoValidator(b"")
        distance = validator._haversine_distance(4.7110, -74.0721, 4.7110, -74.0721)

        assert distance == 0.0

    def test_known_distance(self):
        """Known distance between cities."""
        validator = PhotoValidator(b"")
        # Bogotá to Medellín ~ 240 km straight-line distance
        distance = validator._haversine_distance(
            4.7110, -74.0721,  # Bogotá
            6.2442, -75.5812   # Medellín
        )

        assert 200 < distance < 280  # Approximate straight-line distance

    def test_short_distance(self):
        """Short distance calculation."""
        validator = PhotoValidator(b"")
        # About 1 km apart
        distance = validator._haversine_distance(
            4.7110, -74.0721,
            4.7200, -74.0721
        )

        assert 0.5 < distance < 1.5


# =============================================================================
# JSON FIELD VALIDATORS TESTS
# =============================================================================

from apps.core.validators import (
    CamposFormularioSchema,
    CampoFormularioItem,
    DatosFormularioSchema,
    DatosImportadosSchema,
    ValidacionIASchema,
    MetadataExifSchema,
    ResumenIndicadoresSchema,
    validate_campos_formulario,
    validate_datos_formulario,
    validate_datos_importados,
    validate_validacion_ia,
    validate_metadata_exif,
    validate_resumen_indicadores,
    campos_formulario_validator,
    validacion_ia_validator,
)
from django.core.exceptions import ValidationError
from pydantic import ValidationError as PydanticValidationError


class TestCamposFormularioSchema:
    """Tests for TipoActividad.campos_formulario validation."""

    def test_valid_campos_formulario(self):
        """Valid form fields configuration should pass."""
        data = {
            "fields": [
                {"name": "altura_poda", "type": "number", "label": "Altura de poda (m)", "required": True},
                {"name": "tipo_vegetacion", "type": "select", "options": ["Arborea", "Arbustiva", "Herbacea"]},
                {"name": "observaciones", "type": "textarea", "required": False},
            ]
        }
        result = validate_campos_formulario(data)
        assert "fields" in result
        assert len(result["fields"]) == 3

    def test_empty_campos_formulario(self):
        """Empty data should return default structure."""
        assert validate_campos_formulario(None) == {"fields": []}
        assert validate_campos_formulario({}) == {"fields": []}
        assert validate_campos_formulario([]) == {"fields": []}

    def test_list_format_legacy(self):
        """Legacy list format should be converted to dict with fields key."""
        data = [
            {"name": "campo1", "type": "text"},
            {"name": "campo2", "type": "number"},
        ]
        result = validate_campos_formulario(data)
        assert "fields" in result
        assert len(result["fields"]) == 2

    def test_invalid_field_type_fails(self):
        """Invalid field type should fail validation."""
        data = {
            "fields": [
                {"name": "test", "type": "invalid_type"}
            ]
        }
        with pytest.raises(PydanticValidationError):
            validate_campos_formulario(data)

    def test_select_without_options_fails(self):
        """Select field without options should fail."""
        data = {
            "fields": [
                {"name": "test", "type": "select"}  # Missing options
            ]
        }
        with pytest.raises(PydanticValidationError):
            validate_campos_formulario(data)

    def test_select_with_options_passes(self):
        """Select field with options should pass."""
        data = {
            "fields": [
                {"name": "estado", "type": "select", "options": ["Bueno", "Regular", "Malo"]}
            ]
        }
        result = validate_campos_formulario(data)
        assert result["fields"][0]["options"] == ["Bueno", "Regular", "Malo"]

    def test_duplicate_field_names_fail(self):
        """Duplicate field names should fail."""
        data = {
            "fields": [
                {"name": "campo", "type": "text"},
                {"name": "campo", "type": "number"},  # Duplicate
            ]
        }
        with pytest.raises(PydanticValidationError):
            validate_campos_formulario(data)

    def test_invalid_field_name_format(self):
        """Field names with invalid characters should fail."""
        data = {
            "fields": [
                {"name": "campo con espacios", "type": "text"}
            ]
        }
        with pytest.raises(PydanticValidationError):
            validate_campos_formulario(data)

    def test_field_name_starting_with_number_fails(self):
        """Field name starting with number should fail."""
        data = {
            "fields": [
                {"name": "1campo", "type": "text"}
            ]
        }
        with pytest.raises(PydanticValidationError):
            validate_campos_formulario(data)

    def test_all_field_types(self):
        """All valid field types should pass."""
        data = {
            "fields": [
                {"name": "text_field", "type": "text"},
                {"name": "textarea_field", "type": "textarea"},
                {"name": "number_field", "type": "number"},
                {"name": "select_field", "type": "select", "options": ["a", "b"]},
                {"name": "boolean_field", "type": "boolean"},
                {"name": "date_field", "type": "date"},
                {"name": "time_field", "type": "time"},
            ]
        }
        result = validate_campos_formulario(data)
        assert len(result["fields"]) == 7


class TestValidacionIASchema:
    """Tests for Evidencia.validacion_ia validation."""

    def test_valid_validacion_ia(self):
        """Valid AI validation data should pass."""
        data = {
            "nitidez": 0.95,
            "iluminacion": 0.88,
            "valida": True,
            "confianza": 0.92,
        }
        result = validate_validacion_ia(data)
        assert result["nitidez"] == 0.95
        assert result["valida"] is True

    def test_empty_validacion_ia_defaults(self):
        """Empty data should return defaults."""
        result = validate_validacion_ia(None)
        assert result["nitidez"] == 1.0
        assert result["iluminacion"] == 1.0
        assert result["valida"] is True

    def test_invalid_score_out_of_range(self):
        """Score values outside 0-1 range should fail."""
        data = {
            "nitidez": 1.5,  # Invalid: > 1.0
            "iluminacion": 0.8,
            "valida": True,
        }
        with pytest.raises(PydanticValidationError):
            validate_validacion_ia(data)

    def test_negative_score_fails(self):
        """Negative score should fail."""
        data = {
            "nitidez": -0.5,  # Invalid: < 0.0
            "iluminacion": 0.8,
            "valida": True,
        }
        with pytest.raises(PydanticValidationError):
            validate_validacion_ia(data)

    def test_with_errors_list(self):
        """Validation with errors list should pass."""
        data = {
            "nitidez": 0.3,
            "iluminacion": 0.9,
            "valida": False,
            "errores": ["Image is blurry", "Low contrast"],
        }
        result = validate_validacion_ia(data)
        assert result["valida"] is False
        assert len(result["errores"]) == 2


class TestMetadataExifSchema:
    """Tests for Evidencia.metadata_exif validation."""

    def test_valid_metadata_exif(self):
        """Valid EXIF metadata should pass."""
        data = {
            "make": "Samsung",
            "model": "Galaxy S23",
            "datetime": "2024-01-15 10:30:00",
            "gps": True,
            "latitude": 4.6097,
            "longitude": -74.0817,
        }
        result = validate_metadata_exif(data)
        assert result["make"] == "Samsung"
        assert result["latitude"] == 4.6097

    def test_empty_metadata_exif(self):
        """Empty data should return empty dict."""
        result = validate_metadata_exif(None)
        assert result == {}

    def test_invalid_latitude_out_of_range(self):
        """Latitude outside valid range should fail."""
        data = {
            "latitude": 95.0,  # Invalid: > 90
            "longitude": -74.0,
        }
        with pytest.raises(PydanticValidationError):
            validate_metadata_exif(data)

    def test_invalid_longitude_out_of_range(self):
        """Longitude outside valid range should fail."""
        data = {
            "latitude": 4.0,
            "longitude": -200.0,  # Invalid: < -180
        }
        with pytest.raises(PydanticValidationError):
            validate_metadata_exif(data)

    def test_invalid_orientation(self):
        """Orientation outside 1-8 range should fail."""
        data = {
            "orientation": 10,  # Invalid: > 8
        }
        with pytest.raises(PydanticValidationError):
            validate_metadata_exif(data)

    def test_extra_fields_allowed(self):
        """Extra fields should be allowed (for raw EXIF data)."""
        data = {
            "make": "Apple",
            "custom_field": "custom_value",
            "another_field": 123,
        }
        result = validate_metadata_exif(data)
        assert result["make"] == "Apple"
        assert result["custom_field"] == "custom_value"


class TestDatosFormularioSchema:
    """Tests for RegistroCampo.datos_formulario validation."""

    def test_valid_datos_formulario(self):
        """Valid form data should pass."""
        data = {
            "observaciones": "Trabajo completado",
            "estado_torre": "Bueno",
            "altura_poda": 5.5,
        }
        result = validate_datos_formulario(data)
        assert result["observaciones"] == "Trabajo completado"
        assert result["estado_torre"] == "Bueno"

    def test_empty_datos_formulario(self):
        """Empty data should return empty dict."""
        result = validate_datos_formulario(None)
        assert result == {}

    def test_extra_fields_allowed(self):
        """Extra dynamic fields should be allowed."""
        data = {
            "custom_field": "value",
            "numeric_field": 42,
            "boolean_field": True,
        }
        result = validate_datos_formulario(data)
        assert result["custom_field"] == "value"

    def test_accidente_reportado_field(self):
        """accidente_reportado field should be boolean."""
        data = {
            "accidente_reportado": True,
        }
        result = validate_datos_formulario(data)
        assert result["accidente_reportado"] is True


class TestResumenIndicadoresSchema:
    """Tests for ActaSeguimiento.resumen_indicadores validation."""

    def test_valid_simple_format(self):
        """Valid simple format should pass."""
        data = {
            "gestion": 95.5,
            "ejecucion": 92.0,
            "ambiental": 98.0,
            "seguridad": 100.0,
            "calidad": 94.5,
        }
        result = validate_resumen_indicadores(data)
        assert result["gestion"] == 95.5
        assert result["seguridad"] == 100.0

    def test_empty_resumen_indicadores(self):
        """Empty data should return empty dict."""
        result = validate_resumen_indicadores(None)
        assert result == {}

    def test_indice_global(self):
        """indice_global should be validated."""
        data = {
            "gestion": 95.0,
            "indice_global": 94.2,
        }
        result = validate_resumen_indicadores(data)
        assert result["indice_global"] == 94.2

    def test_invalid_indicator_value_out_of_range(self):
        """Indicator value outside 0-100 should fail."""
        data = {
            "gestion": 150.0,  # Invalid: > 100
        }
        with pytest.raises(PydanticValidationError):
            validate_resumen_indicadores(data)

    def test_negative_indicator_value_fails(self):
        """Negative indicator value should fail."""
        data = {
            "ejecucion": -10.0,  # Invalid: < 0
        }
        with pytest.raises(PydanticValidationError):
            validate_resumen_indicadores(data)


class TestDatosImportadosSchema:
    """Tests for ProgramacionMensual.datos_importados validation."""

    def test_valid_datos_importados(self):
        """Valid import data should pass."""
        data = {
            "archivo_nombre": "programacion_enero.xlsx",
            "fecha_importacion": "2024-01-15 10:30:00",
            "total_filas": 50,
            "filas_procesadas": 48,
            "filas_con_error": 2,
        }
        result = validate_datos_importados(data)
        assert result["archivo_nombre"] == "programacion_enero.xlsx"
        assert result["total_filas"] == 50

    def test_empty_datos_importados(self):
        """Empty data should return empty dict."""
        result = validate_datos_importados(None)
        assert result == {}

    def test_with_actividades_list(self):
        """Data with activities list should pass."""
        data = {
            "actividades": [
                {"torre": "T-001", "tipo_actividad": "PODA-001"},
                {"torre": "T-002", "tipo_actividad": "INS-001"},
            ]
        }
        result = validate_datos_importados(data)
        assert len(result["actividades"]) == 2

    def test_negative_counts_fail(self):
        """Negative row counts should fail."""
        data = {
            "total_filas": -5,  # Invalid: < 0
        }
        with pytest.raises(PydanticValidationError):
            validate_datos_importados(data)


class TestDjangoValidatorWrapper:
    """Tests for Django validator wrapper functions."""

    def test_django_validator_passes_valid_data(self):
        """Django validator should pass valid data."""
        data = {
            "fields": [
                {"name": "test", "type": "text"}
            ]
        }
        # Should not raise
        campos_formulario_validator(data)

    def test_django_validator_raises_validation_error(self):
        """Django validator should raise ValidationError on invalid data."""
        data = {
            "fields": [
                {"name": "test", "type": "invalid"}
            ]
        }
        with pytest.raises(ValidationError) as exc_info:
            campos_formulario_validator(data)
        assert "Invalid JSON structure" in str(exc_info.value)

    def test_validacion_ia_validator(self):
        """validacion_ia validator should work correctly."""
        # Valid data
        validacion_ia_validator({"nitidez": 0.9, "iluminacion": 0.8, "valida": True})

        # Invalid data
        with pytest.raises(ValidationError):
            validacion_ia_validator({"nitidez": 2.0})  # Out of range
