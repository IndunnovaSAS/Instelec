"""
Core utility functions.
"""
from django.conf import settings
from google.cloud import storage
import io
import logging

logger = logging.getLogger(__name__)


def upload_to_gcs(file_content, destination_path: str) -> str:
    """
    Upload file to Google Cloud Storage.

    Args:
        file_content: File content (bytes or file-like object)
        destination_path: Path in the bucket (e.g., 'evidencias/123/foto.jpg')

    Returns:
        Public URL of the uploaded file
    """
    if not settings.GS_BUCKET_NAME:
        # Local development - save to media folder
        from django.core.files.storage import default_storage
        path = default_storage.save(destination_path, io.BytesIO(file_content))
        return default_storage.url(path)

    client = storage.Client(project=settings.GS_PROJECT_ID)
    bucket = client.bucket(settings.GS_BUCKET_NAME)
    blob = bucket.blob(destination_path)

    if isinstance(file_content, bytes):
        blob.upload_from_string(file_content)
    else:
        blob.upload_from_file(file_content)

    blob.make_public()
    return blob.public_url


def download_from_gcs(url: str) -> bytes:
    """
    Download file from Google Cloud Storage.

    Args:
        url: Public URL or gs:// path

    Returns:
        File content as bytes
    """
    if not settings.GS_BUCKET_NAME:
        # Local development
        import requests
        response = requests.get(url)
        return response.content

    # Parse bucket and blob name from URL
    if url.startswith('https://storage.googleapis.com/'):
        path = url.replace('https://storage.googleapis.com/', '')
        bucket_name, blob_name = path.split('/', 1)
    else:
        bucket_name = settings.GS_BUCKET_NAME
        blob_name = url

    client = storage.Client(project=settings.GS_PROJECT_ID)
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    return blob.download_as_bytes()


def format_currency(value, currency='COP'):
    """Format number as currency."""
    if value is None:
        return '-'
    if currency == 'COP':
        return f"${value:,.0f}".replace(',', '.')
    return f"${value:,.2f}"


def format_percentage(value, decimals=1):
    """Format number as percentage."""
    if value is None:
        return '-'
    return f"{value:.{decimals}f}%"


def truncate_string(text: str, max_length: int = 50) -> str:
    """Truncate string with ellipsis."""
    if not text:
        return ''
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + '...'
