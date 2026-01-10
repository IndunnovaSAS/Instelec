"""
Pydantic schemas for JSON field validation.

This module provides validation schemas for all JSONField fields
in the application models to ensure data integrity and consistency.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# =============================================================================
# ACTIVIDADES APP - TipoActividad.campos_formulario
# =============================================================================

class CampoFormularioItem(BaseModel):
    """
    Schema for a single form field definition.

    Used in TipoActividad.campos_formulario to define dynamic form fields.
    """
    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Field identifier (snake_case)"
    )
    type: Literal["text", "textarea", "number", "select", "boolean", "date", "time"] = Field(
        ...,
        description="Field type"
    )
    label: Optional[str] = Field(
        None,
        max_length=100,
        description="Display label for the field"
    )
    required: bool = Field(
        default=False,
        description="Whether the field is required"
    )
    options: Optional[list[str]] = Field(
        None,
        description="Options for select fields"
    )
    default: Optional[Any] = Field(
        None,
        description="Default value for the field"
    )
    min_value: Optional[float] = Field(
        None,
        description="Minimum value for number fields"
    )
    max_value: Optional[float] = Field(
        None,
        description="Maximum value for number fields"
    )
    placeholder: Optional[str] = Field(
        None,
        max_length=200,
        description="Placeholder text"
    )

    @field_validator("name")
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        """Ensure name is in snake_case format."""
        if not v.replace("_", "").isalnum():
            raise ValueError("Field name must contain only alphanumeric characters and underscores")
        if v[0].isdigit():
            raise ValueError("Field name cannot start with a number")
        return v.lower()

    @model_validator(mode="after")
    def validate_options_for_select(self) -> "CampoFormularioItem":
        """Ensure select fields have options."""
        if self.type == "select" and not self.options:
            raise ValueError("Select fields must have at least one option")
        return self


class CamposFormularioSchema(BaseModel):
    """
    Schema for TipoActividad.campos_formulario JSON field.

    Example:
        {
            "fields": [
                {"name": "altura_poda", "type": "number", "label": "Altura de poda (m)", "required": true},
                {"name": "tipo_vegetacion", "type": "select", "options": ["Arborea", "Arbustiva"]}
            ]
        }
    """
    model_config = ConfigDict(extra="forbid")

    fields: list[CampoFormularioItem] = Field(
        default_factory=list,
        description="List of form field definitions"
    )

    @field_validator("fields")
    @classmethod
    def validate_unique_names(cls, v: list[CampoFormularioItem]) -> list[CampoFormularioItem]:
        """Ensure all field names are unique."""
        names = [field.name for field in v]
        if len(names) != len(set(names)):
            raise ValueError("Field names must be unique")
        return v


# =============================================================================
# ACTIVIDADES APP - ProgramacionMensual.datos_importados
# =============================================================================

class ActividadImportada(BaseModel):
    """Schema for a single imported activity from Excel."""
    model_config = ConfigDict(extra="allow")  # Allow extra fields from Excel

    torre: str = Field(..., description="Tower identifier")
    tipo_actividad: str = Field(..., description="Activity type code")
    fecha_programada: Optional[str] = Field(None, description="Scheduled date")
    prioridad: Optional[str] = Field(None, description="Priority level")
    observaciones: Optional[str] = Field(None, description="Notes")


class DatosImportadosSchema(BaseModel):
    """
    Schema for ProgramacionMensual.datos_importados JSON field.

    Stores raw data imported from client's Excel file.
    """
    model_config = ConfigDict(extra="allow")

    archivo_nombre: Optional[str] = Field(None, description="Original file name")
    fecha_importacion: Optional[str] = Field(None, description="Import datetime")
    usuario_importacion: Optional[str] = Field(None, description="User who imported")
    total_filas: Optional[int] = Field(None, ge=0, description="Total rows in file")
    filas_procesadas: Optional[int] = Field(None, ge=0, description="Processed rows")
    filas_con_error: Optional[int] = Field(None, ge=0, description="Rows with errors")
    errores: Optional[list[dict]] = Field(None, description="Import errors")
    actividades: Optional[list[ActividadImportada]] = Field(
        None,
        description="Imported activities data"
    )


# =============================================================================
# CAMPO APP - RegistroCampo.datos_formulario
# =============================================================================

class DatosFormularioSchema(BaseModel):
    """
    Schema for RegistroCampo.datos_formulario JSON field.

    This schema is flexible as the actual fields depend on TipoActividad.
    It validates common fields and allows additional dynamic fields.

    Example:
        {
            "observaciones": "Trabajo realizado correctamente",
            "estado_torre": "Bueno",
            "altura_poda": 5.5
        }
    """
    model_config = ConfigDict(extra="allow")  # Allow dynamic fields

    # Common optional fields that may appear across activity types
    observaciones: Optional[str] = Field(
        None,
        max_length=2000,
        description="General observations"
    )
    estado_torre: Optional[str] = Field(
        None,
        description="Tower condition"
    )
    accidente_reportado: Optional[bool] = Field(
        None,
        description="Whether an accident was reported"
    )

    @model_validator(mode="before")
    @classmethod
    def validate_no_null_values(cls, data: dict) -> dict:
        """Remove None values from the data."""
        if isinstance(data, dict):
            return {k: v for k, v in data.items() if v is not None}
        return data


# =============================================================================
# CAMPO APP - Evidencia.validacion_ia
# =============================================================================

class ValidacionIASchema(BaseModel):
    """
    Schema for Evidencia.validacion_ia JSON field.

    Stores AI validation results for evidence photos.

    Example:
        {
            "nitidez": 0.95,
            "iluminacion": 0.88,
            "valida": true,
            "confianza": 0.92,
            "mensaje": "Imagen aceptada"
        }
    """
    model_config = ConfigDict(extra="allow")

    nitidez: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Sharpness score (0.0 to 1.0)"
    )
    iluminacion: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Lighting score (0.0 to 1.0)"
    )
    valida: bool = Field(
        default=True,
        description="Whether the photo is valid"
    )
    confianza: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score"
    )
    contraste: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Contrast score"
    )
    mensaje: Optional[str] = Field(
        None,
        max_length=500,
        description="Validation message"
    )
    errores: Optional[list[str]] = Field(
        None,
        description="List of validation errors"
    )
    advertencias: Optional[list[str]] = Field(
        None,
        description="List of validation warnings"
    )

    @model_validator(mode="after")
    def validate_scores_when_invalid(self) -> "ValidacionIASchema":
        """If photo is invalid, at least one score should be low."""
        if not self.valida:
            min_score = min(self.nitidez, self.iluminacion)
            if min_score > 0.8 and not self.errores:
                # Add warning if marked invalid but scores are high
                if self.advertencias is None:
                    self.advertencias = []
                self.advertencias.append(
                    "Photo marked as invalid but quality scores are high"
                )
        return self


# =============================================================================
# CAMPO APP - Evidencia.metadata_exif
# =============================================================================

class GPSInfo(BaseModel):
    """Schema for GPS information in EXIF metadata."""
    model_config = ConfigDict(extra="allow")

    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    altitude: Optional[float] = Field(None)
    timestamp: Optional[str] = Field(None)


class MetadataExifSchema(BaseModel):
    """
    Schema for Evidencia.metadata_exif JSON field.

    Stores EXIF metadata extracted from photos.

    Example:
        {
            "make": "Samsung",
            "model": "Galaxy S23",
            "datetime": "2024-01-15 10:30:00",
            "gps": true,
            "latitude": 4.6097,
            "longitude": -74.0817
        }
    """
    model_config = ConfigDict(extra="allow")

    make: Optional[str] = Field(
        None,
        max_length=100,
        description="Camera manufacturer"
    )
    model: Optional[str] = Field(
        None,
        max_length=100,
        description="Camera model"
    )
    datetime: Optional[str] = Field(
        None,
        description="Photo capture datetime"
    )
    gps: Optional[bool] = Field(
        None,
        description="Whether GPS info is present"
    )
    latitude: Optional[float] = Field(
        None,
        ge=-90,
        le=90,
        description="GPS latitude"
    )
    longitude: Optional[float] = Field(
        None,
        ge=-180,
        le=180,
        description="GPS longitude"
    )
    altitude: Optional[float] = Field(
        None,
        description="GPS altitude in meters"
    )
    orientation: Optional[int] = Field(
        None,
        ge=1,
        le=8,
        description="Image orientation (1-8)"
    )
    width: Optional[int] = Field(
        None,
        gt=0,
        description="Image width in pixels"
    )
    height: Optional[int] = Field(
        None,
        gt=0,
        description="Image height in pixels"
    )
    software: Optional[str] = Field(
        None,
        max_length=100,
        description="Software used"
    )
    gps_info: Optional[GPSInfo] = Field(
        None,
        description="Detailed GPS information"
    )


# =============================================================================
# INDICADORES APP - ActaSeguimiento.resumen_indicadores
# =============================================================================

class IndicadorResumen(BaseModel):
    """Schema for a single indicator summary."""
    model_config = ConfigDict(extra="allow")

    valor: float = Field(..., ge=0, le=100, description="Indicator value")
    meta: Optional[float] = Field(None, ge=0, le=100, description="Target value")
    cumple: Optional[bool] = Field(None, description="Whether target is met")
    tendencia: Optional[Literal["subiendo", "bajando", "estable"]] = Field(
        None,
        description="Trend direction"
    )


class ResumenIndicadoresSchema(BaseModel):
    """
    Schema for ActaSeguimiento.resumen_indicadores JSON field.

    Stores indicator summary for monthly follow-up meetings.

    Example (simple format):
        {
            "gestion": 95.5,
            "ejecucion": 92.0,
            "ambiental": 98.0,
            "seguridad": 100.0,
            "calidad": 94.5
        }

    Example (detailed format):
        {
            "gestion": {"valor": 95.5, "meta": 95.0, "cumple": true},
            "ejecucion": {"valor": 92.0, "meta": 90.0, "cumple": true},
            "indice_global": 94.2
        }
    """
    model_config = ConfigDict(extra="allow")

    # Indicator values - can be simple float or detailed object
    gestion: Optional[float | IndicadorResumen] = Field(
        None,
        description="Management indicator"
    )
    ejecucion: Optional[float | IndicadorResumen] = Field(
        None,
        description="Execution indicator"
    )
    ambiental: Optional[float | IndicadorResumen] = Field(
        None,
        description="Environmental indicator"
    )
    seguridad: Optional[float | IndicadorResumen] = Field(
        None,
        description="Safety indicator"
    )
    calidad: Optional[float | IndicadorResumen] = Field(
        None,
        description="Quality indicator"
    )
    cronograma: Optional[float | IndicadorResumen] = Field(
        None,
        description="Schedule indicator"
    )
    indice_global: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Global performance index"
    )
    periodo: Optional[str] = Field(
        None,
        description="Period (e.g., '2024-01')"
    )
    fecha_calculo: Optional[str] = Field(
        None,
        description="Calculation datetime"
    )

    @field_validator("gestion", "ejecucion", "ambiental", "seguridad", "calidad", "cronograma", mode="before")
    @classmethod
    def validate_indicator_value(cls, v):
        """Validate indicator value is in valid range."""
        if isinstance(v, (int, float)):
            if not 0 <= v <= 100:
                raise ValueError("Indicator value must be between 0 and 100")
        return v


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def validate_campos_formulario(data: dict | list | None) -> dict:
    """
    Validate TipoActividad.campos_formulario field.

    Args:
        data: Raw JSON data to validate

    Returns:
        Validated data as dict

    Raises:
        ValueError: If validation fails
    """
    if data is None or data == {} or data == []:
        return {"fields": []}

    # Handle list format (legacy)
    if isinstance(data, list):
        data = {"fields": data}

    schema = CamposFormularioSchema.model_validate(data)
    return schema.model_dump()


def validate_datos_importados(data: dict | None) -> dict:
    """
    Validate ProgramacionMensual.datos_importados field.

    Args:
        data: Raw JSON data to validate

    Returns:
        Validated data as dict

    Raises:
        ValueError: If validation fails
    """
    if data is None:
        return {}

    schema = DatosImportadosSchema.model_validate(data)
    return schema.model_dump(exclude_none=True)


def validate_datos_formulario(data: dict | None) -> dict:
    """
    Validate RegistroCampo.datos_formulario field.

    Args:
        data: Raw JSON data to validate

    Returns:
        Validated data as dict

    Raises:
        ValueError: If validation fails
    """
    if data is None:
        return {}

    schema = DatosFormularioSchema.model_validate(data)
    return schema.model_dump(exclude_none=True)


def validate_validacion_ia(data: dict | None) -> dict:
    """
    Validate Evidencia.validacion_ia field.

    Args:
        data: Raw JSON data to validate

    Returns:
        Validated data as dict

    Raises:
        ValueError: If validation fails
    """
    if data is None:
        return {"nitidez": 1.0, "iluminacion": 1.0, "valida": True}

    schema = ValidacionIASchema.model_validate(data)
    return schema.model_dump(exclude_none=True)


def validate_metadata_exif(data: dict | None) -> dict:
    """
    Validate Evidencia.metadata_exif field.

    Args:
        data: Raw JSON data to validate

    Returns:
        Validated data as dict

    Raises:
        ValueError: If validation fails
    """
    if data is None:
        return {}

    schema = MetadataExifSchema.model_validate(data)
    return schema.model_dump(exclude_none=True)


def validate_resumen_indicadores(data: dict | None) -> dict:
    """
    Validate ActaSeguimiento.resumen_indicadores field.

    Args:
        data: Raw JSON data to validate

    Returns:
        Validated data as dict

    Raises:
        ValueError: If validation fails
    """
    if data is None:
        return {}

    schema = ResumenIndicadoresSchema.model_validate(data)
    return schema.model_dump(exclude_none=True)


# =============================================================================
# DJANGO VALIDATOR WRAPPER
# =============================================================================

def create_json_validator(validate_func):
    """
    Create a Django validator function from a Pydantic validation function.

    Args:
        validate_func: Pydantic validation function

    Returns:
        Django validator function
    """
    from django.core.exceptions import ValidationError as DjangoValidationError
    from pydantic import ValidationError as PydanticValidationError

    def django_validator(value):
        try:
            validate_func(value)
        except PydanticValidationError as e:
            errors = []
            for error in e.errors():
                loc = " -> ".join(str(x) for x in error["loc"]) if error["loc"] else "root"
                errors.append(f"{loc}: {error['msg']}")
            raise DjangoValidationError(
                "Invalid JSON structure: " + "; ".join(errors)
            )
        except Exception as e:
            raise DjangoValidationError(f"Validation error: {str(e)}")

    return django_validator


# Pre-built Django validators
campos_formulario_validator = create_json_validator(validate_campos_formulario)
datos_importados_validator = create_json_validator(validate_datos_importados)
datos_formulario_validator = create_json_validator(validate_datos_formulario)
validacion_ia_validator = create_json_validator(validate_validacion_ia)
metadata_exif_validator = create_json_validator(validate_metadata_exif)
resumen_indicadores_validator = create_json_validator(validate_resumen_indicadores)
