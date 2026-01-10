"""
Photo validators for field evidence.

Validates images for:
- Quality (blur, brightness, contrast)
- Metadata (GPS, timestamp)
- Content requirements (before/during/after)
- Size and format
- MIME type validation using magic bytes
"""

import io
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Tuple

import magic
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)


# =============================================================================
# MIME Type Validation with Magic Bytes
# =============================================================================

class MimeTypeValidator:
    """
    Validates file MIME types using magic bytes (file signatures).

    This validator checks the actual file content, not just the extension,
    to prevent malicious file uploads disguised with fake extensions.
    """

    # Allowed MIME types for images
    ALLOWED_IMAGE_TYPES = {
        'image/jpeg',
        'image/png',
        'image/webp',
    }

    # Allowed MIME types for documents
    ALLOWED_DOCUMENT_TYPES = {
        'application/pdf',
        'application/msword',  # .doc
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',  # .pptx
    }

    # Magic bytes signatures for additional verification
    # These are the first bytes of each file type
    MAGIC_SIGNATURES = {
        'image/jpeg': [
            b'\xff\xd8\xff\xe0',  # JFIF
            b'\xff\xd8\xff\xe1',  # EXIF
            b'\xff\xd8\xff\xe2',  # SPIFF
            b'\xff\xd8\xff\xdb',  # Quantization table
            b'\xff\xd8\xff\xee',  # Adobe
        ],
        'image/png': [
            b'\x89PNG\r\n\x1a\n',
        ],
        'image/webp': [
            b'RIFF',  # WebP starts with RIFF, followed by file size and WEBP
        ],
        'application/pdf': [
            b'%PDF-',
        ],
        'application/msword': [
            b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',  # OLE compound document
        ],
        'application/vnd.openxmlformats-officedocument': [
            b'PK\x03\x04',  # ZIP-based (OOXML)
        ],
    }

    def __init__(self, file_bytes: bytes, filename: str = ""):
        """
        Initialize the validator.

        Args:
            file_bytes: The raw file content
            filename: Original filename (used for logging, not for validation)
        """
        self.file_bytes = file_bytes
        self.filename = filename
        self._detected_mime = None

    @property
    def detected_mime_type(self) -> str:
        """Get the detected MIME type using python-magic."""
        if self._detected_mime is None:
            try:
                self._detected_mime = magic.from_buffer(self.file_bytes, mime=True)
            except Exception as e:
                logger.error(f"Error detecting MIME type for {self.filename}: {e}")
                self._detected_mime = 'application/octet-stream'
        return self._detected_mime

    def _verify_magic_bytes(self, expected_mime: str) -> bool:
        """
        Verify the file starts with expected magic bytes.

        This is an additional security layer beyond python-magic.
        """
        if expected_mime.startswith('application/vnd.openxmlformats-officedocument'):
            # All OOXML formats use the same ZIP signature
            signatures = self.MAGIC_SIGNATURES.get('application/vnd.openxmlformats-officedocument', [])
        else:
            signatures = self.MAGIC_SIGNATURES.get(expected_mime, [])

        if not signatures:
            # No signature defined for this type, rely on python-magic only
            return True

        # Special handling for WebP (RIFF....WEBP)
        if expected_mime == 'image/webp':
            return (
                self.file_bytes[:4] == b'RIFF' and
                len(self.file_bytes) >= 12 and
                self.file_bytes[8:12] == b'WEBP'
            )

        # Check if file starts with any of the valid signatures
        for sig in signatures:
            if self.file_bytes[:len(sig)] == sig:
                return True

        return False

    def validate_image(self) -> Tuple[bool, str]:
        """
        Validate that the file is an allowed image type.

        Returns:
            Tuple of (is_valid, error_message)
        """
        detected = self.detected_mime_type

        # Check if detected MIME type is allowed
        if detected not in self.ALLOWED_IMAGE_TYPES:
            allowed_str = ', '.join(sorted(self.ALLOWED_IMAGE_TYPES))
            return False, f"Tipo de archivo no permitido: {detected}. Tipos permitidos: {allowed_str}"

        # Verify magic bytes match
        if not self._verify_magic_bytes(detected):
            logger.warning(
                f"Magic bytes mismatch for {self.filename}: "
                f"detected={detected}, bytes={self.file_bytes[:16].hex()}"
            )
            return False, f"El contenido del archivo no coincide con el tipo declarado ({detected})"

        return True, ""

    def validate_document(self) -> Tuple[bool, str]:
        """
        Validate that the file is an allowed document type.

        Returns:
            Tuple of (is_valid, error_message)
        """
        detected = self.detected_mime_type

        # Check if detected MIME type is allowed
        if detected not in self.ALLOWED_DOCUMENT_TYPES:
            allowed_str = ', '.join(sorted(self.ALLOWED_DOCUMENT_TYPES))
            return False, f"Tipo de documento no permitido: {detected}. Tipos permitidos: {allowed_str}"

        # Verify magic bytes match
        if not self._verify_magic_bytes(detected):
            logger.warning(
                f"Magic bytes mismatch for {self.filename}: "
                f"detected={detected}, bytes={self.file_bytes[:16].hex()}"
            )
            return False, f"El contenido del archivo no coincide con el tipo declarado ({detected})"

        return True, ""

    def validate_image_or_document(self) -> Tuple[bool, str]:
        """
        Validate that the file is either an allowed image or document type.

        Returns:
            Tuple of (is_valid, error_message)
        """
        detected = self.detected_mime_type

        all_allowed = self.ALLOWED_IMAGE_TYPES | self.ALLOWED_DOCUMENT_TYPES

        if detected not in all_allowed:
            return False, f"Tipo de archivo no permitido: {detected}"

        if not self._verify_magic_bytes(detected):
            logger.warning(
                f"Magic bytes mismatch for {self.filename}: "
                f"detected={detected}, bytes={self.file_bytes[:16].hex()}"
            )
            return False, f"El contenido del archivo no coincide con el tipo declarado ({detected})"

        return True, ""


def validate_image_mime_type(file_bytes: bytes, filename: str = "") -> None:
    """
    Django validator function for image uploads.

    Raises ValidationError if the file is not a valid image type.

    Args:
        file_bytes: The raw file content
        filename: Original filename for logging

    Raises:
        ValidationError: If validation fails
    """
    validator = MimeTypeValidator(file_bytes, filename)
    is_valid, error_message = validator.validate_image()

    if not is_valid:
        raise ValidationError(error_message)


def validate_document_mime_type(file_bytes: bytes, filename: str = "") -> None:
    """
    Django validator function for document uploads.

    Raises ValidationError if the file is not a valid document type.

    Args:
        file_bytes: The raw file content
        filename: Original filename for logging

    Raises:
        ValidationError: If validation fails
    """
    validator = MimeTypeValidator(file_bytes, filename)
    is_valid, error_message = validator.validate_document()

    if not is_valid:
        raise ValidationError(error_message)


def validate_evidence_mime_type(file_bytes: bytes, filename: str = "") -> None:
    """
    Django validator function for evidence uploads (images only).

    This is specifically for field evidence photos which must be images.

    Args:
        file_bytes: The raw file content
        filename: Original filename for logging

    Raises:
        ValidationError: If validation fails
    """
    validator = MimeTypeValidator(file_bytes, filename)
    is_valid, error_message = validator.validate_image()

    if not is_valid:
        raise ValidationError(error_message)


def validate_signature_mime_type(file_bytes: bytes, filename: str = "") -> None:
    """
    Django validator function for signature uploads.

    Signatures must be PNG images (typically with transparency).

    Args:
        file_bytes: The raw file content
        filename: Original filename for logging

    Raises:
        ValidationError: If validation fails
    """
    validator = MimeTypeValidator(file_bytes, filename)
    detected = validator.detected_mime_type

    # Signatures should be PNG
    if detected != 'image/png':
        raise ValidationError(
            f"Las firmas deben ser imagenes PNG. Tipo detectado: {detected}"
        )

    if not validator._verify_magic_bytes('image/png'):
        raise ValidationError(
            "El contenido del archivo no es una imagen PNG valida"
        )


@dataclass
class ValidationResult:
    """Result of photo validation."""
    is_valid: bool
    score: float  # 0.0 to 1.0
    errors: list[str]
    warnings: list[str]
    metadata: dict


class PhotoValidator:
    """Validates field evidence photos."""

    # Minimum requirements
    MIN_WIDTH = 640
    MIN_HEIGHT = 480
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
    ALLOWED_FORMATS = {'JPEG', 'PNG', 'WEBP'}
    MIN_BRIGHTNESS = 0.15
    MAX_BRIGHTNESS = 0.95
    MIN_CONTRAST = 0.1
    MIN_SHARPNESS = 0.3
    MAX_LOCATION_DIFF_KM = 1.0  # Max distance from expected location
    MAX_TIME_DIFF_HOURS = 24  # Max time difference from expected

    def __init__(self, image_bytes: bytes):
        self.image_bytes = image_bytes
        self.image = None
        self.errors = []
        self.warnings = []
        self.metadata = {}

    def validate(
        self,
        expected_lat: Optional[float] = None,
        expected_lon: Optional[float] = None,
        expected_date: Optional[datetime] = None,
        photo_type: str = 'DURANTE'
    ) -> ValidationResult:
        """
        Run all validations on the photo.

        Args:
            expected_lat: Expected latitude for GPS validation
            expected_lon: Expected longitude for GPS validation
            expected_date: Expected date/time for timestamp validation
            photo_type: Type of photo (ANTES, DURANTE, DESPUES)

        Returns:
            ValidationResult with validation details
        """
        self.errors = []
        self.warnings = []
        self.metadata = {}

        try:
            self.image = Image.open(io.BytesIO(self.image_bytes))
        except (IOError, OSError) as e:
            logger.warning(f"Failed to open image: {e}")
            return ValidationResult(
                is_valid=False,
                score=0.0,
                errors=[f"Cannot open image: {str(e)}"],
                warnings=[],
                metadata={}
            )

        # Run validations
        scores = []

        # 1. Format and size validation
        format_score = self._validate_format()
        scores.append(format_score)

        # 2. Resolution validation
        resolution_score = self._validate_resolution()
        scores.append(resolution_score)

        # 3. Quality validation (brightness, contrast, sharpness)
        quality_score = self._validate_quality()
        scores.append(quality_score)

        # 4. Metadata extraction and validation
        self._extract_metadata()

        # 5. GPS validation if expected location provided
        if expected_lat and expected_lon:
            gps_score = self._validate_gps(expected_lat, expected_lon)
            scores.append(gps_score)

        # 6. Timestamp validation if expected date provided
        if expected_date:
            time_score = self._validate_timestamp(expected_date)
            scores.append(time_score)

        # Calculate overall score
        overall_score = sum(scores) / len(scores) if scores else 0.0

        # Determine if valid
        is_valid = len(self.errors) == 0 and overall_score >= 0.6

        return ValidationResult(
            is_valid=is_valid,
            score=overall_score,
            errors=self.errors,
            warnings=self.warnings,
            metadata=self.metadata
        )

    def _validate_format(self) -> float:
        """Validate image format and file size."""
        # Check format
        if self.image.format not in self.ALLOWED_FORMATS:
            self.errors.append(f"Format not allowed: {self.image.format}. Use: {', '.join(self.ALLOWED_FORMATS)}")
            return 0.0

        # Check file size
        if len(self.image_bytes) > self.MAX_FILE_SIZE:
            size_mb = len(self.image_bytes) / (1024 * 1024)
            self.errors.append(f"File too large: {size_mb:.1f}MB. Max: {self.MAX_FILE_SIZE / (1024*1024):.0f}MB")
            return 0.5

        return 1.0

    def _validate_resolution(self) -> float:
        """Validate image resolution."""
        width, height = self.image.size

        if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
            self.errors.append(f"Resolution too low: {width}x{height}. Min: {self.MIN_WIDTH}x{self.MIN_HEIGHT}")
            return 0.0

        if width < 1280 or height < 720:
            self.warnings.append(f"Low resolution: {width}x{height}. Recommended: 1280x720 or higher")
            return 0.7

        return 1.0

    def _validate_quality(self) -> float:
        """Validate image quality (brightness, contrast, sharpness)."""
        import numpy as np

        # Convert to numpy array
        img_array = np.array(self.image.convert('RGB'))

        # Calculate brightness
        brightness = np.mean(img_array) / 255.0
        self.metadata['brightness'] = round(brightness, 2)

        if brightness < self.MIN_BRIGHTNESS:
            self.errors.append("Image too dark")
            brightness_score = 0.0
        elif brightness > self.MAX_BRIGHTNESS:
            self.errors.append("Image overexposed")
            brightness_score = 0.0
        else:
            brightness_score = 1.0

        # Calculate contrast
        contrast = np.std(img_array) / 128.0
        self.metadata['contrast'] = round(contrast, 2)

        if contrast < self.MIN_CONTRAST:
            self.warnings.append("Low contrast image")
            contrast_score = 0.5
        else:
            contrast_score = 1.0

        # Calculate sharpness (Laplacian variance)
        gray = np.mean(img_array, axis=2) if len(img_array.shape) == 3 else img_array
        laplacian_var = np.var(np.gradient(np.gradient(gray)))
        sharpness = min(laplacian_var / 500.0, 1.0)
        self.metadata['sharpness'] = round(sharpness, 2)

        if sharpness < self.MIN_SHARPNESS:
            self.errors.append("Image is blurry")
            sharpness_score = 0.0
        else:
            sharpness_score = 1.0

        return (brightness_score + contrast_score + sharpness_score) / 3

    def _extract_metadata(self):
        """Extract EXIF metadata from image."""
        try:
            exif_data = self.image._getexif()
            if not exif_data:
                self.warnings.append("No EXIF metadata found")
                return

            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)

                if tag == 'GPSInfo':
                    gps_info = {}
                    for gps_tag_id, gps_value in value.items():
                        gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                        gps_info[gps_tag] = gps_value
                    self.metadata['gps_info'] = gps_info

                    # Extract coordinates
                    lat, lon = self._get_gps_coordinates(gps_info)
                    if lat and lon:
                        self.metadata['latitude'] = lat
                        self.metadata['longitude'] = lon

                elif tag == 'DateTime' or tag == 'DateTimeOriginal':
                    self.metadata['datetime'] = value

                elif tag == 'Make':
                    self.metadata['camera_make'] = value

                elif tag == 'Model':
                    self.metadata['camera_model'] = value

        except (AttributeError, KeyError, TypeError) as e:
            logger.warning(f"Error extracting EXIF metadata: {e}")
            self.warnings.append("Could not extract EXIF metadata")

    def _get_gps_coordinates(self, gps_info: dict) -> Tuple[Optional[float], Optional[float]]:
        """Extract GPS coordinates from GPS info dict."""
        try:
            lat = gps_info.get('GPSLatitude')
            lat_ref = gps_info.get('GPSLatitudeRef')
            lon = gps_info.get('GPSLongitude')
            lon_ref = gps_info.get('GPSLongitudeRef')

            if not all([lat, lat_ref, lon, lon_ref]):
                return None, None

            # Convert to decimal degrees
            lat_decimal = self._convert_to_degrees(lat)
            lon_decimal = self._convert_to_degrees(lon)

            if lat_ref == 'S':
                lat_decimal = -lat_decimal
            if lon_ref == 'W':
                lon_decimal = -lon_decimal

            return lat_decimal, lon_decimal

        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            return None, None

    def _convert_to_degrees(self, value) -> float:
        """Convert GPS coordinates to decimal degrees."""
        d = float(value[0])
        m = float(value[1])
        s = float(value[2])
        return d + (m / 60.0) + (s / 3600.0)

    def _validate_gps(self, expected_lat: float, expected_lon: float) -> float:
        """Validate GPS coordinates match expected location."""
        actual_lat = self.metadata.get('latitude')
        actual_lon = self.metadata.get('longitude')

        if not actual_lat or not actual_lon:
            self.warnings.append("No GPS coordinates in image")
            return 0.5

        # Calculate distance using Haversine formula
        distance = self._haversine_distance(
            expected_lat, expected_lon,
            actual_lat, actual_lon
        )

        self.metadata['distance_km'] = round(distance, 2)

        if distance > self.MAX_LOCATION_DIFF_KM:
            self.errors.append(f"Location too far from expected: {distance:.1f}km (max: {self.MAX_LOCATION_DIFF_KM}km)")
            return 0.0

        if distance > self.MAX_LOCATION_DIFF_KM * 0.5:
            self.warnings.append(f"Location differs by {distance:.1f}km from expected")
            return 0.7

        return 1.0

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points in km using Haversine formula."""
        import math

        R = 6371  # Earth radius in km

        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        return R * c

    def _validate_timestamp(self, expected_date: datetime) -> float:
        """Validate image timestamp matches expected date."""
        datetime_str = self.metadata.get('datetime')

        if not datetime_str:
            self.warnings.append("No timestamp in image metadata")
            return 0.5

        try:
            # Parse EXIF datetime format
            actual_date = datetime.strptime(datetime_str, '%Y:%m:%d %H:%M:%S')
            self.metadata['parsed_datetime'] = actual_date.isoformat()

            # Calculate time difference
            time_diff = abs((actual_date - expected_date).total_seconds() / 3600)
            self.metadata['time_diff_hours'] = round(time_diff, 1)

            if time_diff > self.MAX_TIME_DIFF_HOURS:
                self.errors.append(f"Image date differs by {time_diff:.0f} hours from expected")
                return 0.0

            if time_diff > 12:
                self.warnings.append(f"Image date differs by {time_diff:.0f} hours")
                return 0.7

            return 1.0

        except ValueError:
            self.warnings.append("Could not parse image timestamp")
            return 0.5


def validate_evidence_photo(
    image_bytes: bytes,
    expected_lat: Optional[float] = None,
    expected_lon: Optional[float] = None,
    expected_date: Optional[datetime] = None,
    photo_type: str = 'DURANTE'
) -> dict:
    """
    Validate an evidence photo.

    Args:
        image_bytes: Raw image bytes
        expected_lat: Expected latitude
        expected_lon: Expected longitude
        expected_date: Expected capture date
        photo_type: Type (ANTES, DURANTE, DESPUES)

    Returns:
        Dictionary with validation results
    """
    validator = PhotoValidator(image_bytes)
    result = validator.validate(expected_lat, expected_lon, expected_date, photo_type)

    return {
        'valid': result.is_valid,
        'score': result.score,
        'errors': result.errors,
        'warnings': result.warnings,
        'metadata': result.metadata,
        'message': 'Photo is valid' if result.is_valid else '; '.join(result.errors)
    }


def validate_photo_set(photos: list[dict]) -> dict:
    """
    Validate a complete set of evidence photos (ANTES, DURANTE, DESPUES).

    Args:
        photos: List of dicts with 'type' and 'bytes' keys

    Returns:
        Dictionary with validation results for the set
    """
    required_types = {'ANTES', 'DURANTE', 'DESPUES'}
    found_types = set()
    results = {}
    all_valid = True

    for photo in photos:
        photo_type = photo.get('type', 'DURANTE')
        photo_bytes = photo.get('bytes')

        if not photo_bytes:
            continue

        found_types.add(photo_type)

        validation = validate_evidence_photo(
            photo_bytes,
            photo.get('lat'),
            photo.get('lon'),
            photo.get('date'),
            photo_type
        )

        results[photo_type] = validation
        if not validation['valid']:
            all_valid = False

    missing_types = required_types - found_types

    return {
        'all_valid': all_valid and len(missing_types) == 0,
        'missing_types': list(missing_types),
        'results': results,
        'message': f"Missing photo types: {', '.join(missing_types)}" if missing_types else (
            "All photos valid" if all_valid else "Some photos failed validation"
        )
    }
