"""
API endpoints for field records (Django Ninja).
"""
from ninja import Router, Schema, File, UploadedFile
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal

from .models import RegistroCampo, Evidencia
from .tasks import procesar_evidencia

router = Router()


class RegistroIn(Schema):
    actividad_id: UUID
    datos_formulario: dict
    observaciones: str = ""
    latitud_fin: Decimal
    longitud_fin: Decimal


class RegistroSyncIn(Schema):
    registros: List[RegistroIn]


class EvidenciaOut(Schema):
    id: UUID
    tipo: str
    url_original: str
    url_thumbnail: str
    latitud: Optional[Decimal]
    longitud: Optional[Decimal]
    fecha_captura: datetime
    es_valida: bool


class RegistroOut(Schema):
    id: UUID
    actividad_id: UUID
    fecha_inicio: datetime
    fecha_fin: Optional[datetime]
    dentro_poligono: Optional[bool]
    sincronizado: bool
    total_evidencias: int


class RegistroDetailOut(RegistroOut):
    datos_formulario: dict
    observaciones: str
    evidencias: List[EvidenciaOut]


class SyncResultOut(Schema):
    id: str
    status: str
    message: str = ""


@router.get('/registros', response=List[RegistroOut])
def listar_registros(request, actividad_id: UUID = None):
    """List field records, optionally filtered by activity."""
    qs = RegistroCampo.objects.all()

    if actividad_id:
        qs = qs.filter(actividad_id=actividad_id)

    return [
        RegistroOut(
            id=r.id,
            actividad_id=r.actividad_id,
            fecha_inicio=r.fecha_inicio,
            fecha_fin=r.fecha_fin,
            dentro_poligono=r.dentro_poligono,
            sincronizado=r.sincronizado,
            total_evidencias=r.total_evidencias,
        )
        for r in qs
    ]


@router.get('/registros/{registro_id}', response=RegistroDetailOut)
def obtener_registro(request, registro_id: UUID):
    """Get field record details."""
    registro = RegistroCampo.objects.prefetch_related('evidencias').get(id=registro_id)

    evidencias = [
        EvidenciaOut(
            id=e.id,
            tipo=e.tipo,
            url_original=e.url_original,
            url_thumbnail=e.url_thumbnail or e.url_original,
            latitud=e.latitud,
            longitud=e.longitud,
            fecha_captura=e.fecha_captura,
            es_valida=e.es_valida,
        )
        for e in registro.evidencias.all()
    ]

    return RegistroDetailOut(
        id=registro.id,
        actividad_id=registro.actividad_id,
        fecha_inicio=registro.fecha_inicio,
        fecha_fin=registro.fecha_fin,
        dentro_poligono=registro.dentro_poligono,
        sincronizado=registro.sincronizado,
        total_evidencias=registro.total_evidencias,
        datos_formulario=registro.datos_formulario,
        observaciones=registro.observaciones,
        evidencias=evidencias,
    )


@router.post('/registros/sync', response=List[SyncResultOut])
def sincronizar_registros(request, data: RegistroSyncIn):
    """
    Sync multiple field records from mobile app.
    Used when device comes back online.
    """
    from django.utils import timezone
    from apps.actividades.models import Actividad

    resultados = []

    for reg in data.registros:
        try:
            registro = RegistroCampo.objects.get(actividad_id=reg.actividad_id)

            # Update record
            registro.datos_formulario = reg.datos_formulario
            registro.observaciones = reg.observaciones
            registro.latitud_fin = reg.latitud_fin
            registro.longitud_fin = reg.longitud_fin
            registro.fecha_fin = timezone.now()
            registro.sincronizado = True
            registro.fecha_sincronizacion = timezone.now()
            registro.save()

            # Update activity status
            actividad = registro.actividad
            actividad.estado = Actividad.Estado.COMPLETADA
            actividad.save(update_fields=['estado', 'updated_at'])

            resultados.append(SyncResultOut(
                id=str(reg.actividad_id),
                status='ok',
                message='Sincronizado correctamente'
            ))

        except RegistroCampo.DoesNotExist:
            resultados.append(SyncResultOut(
                id=str(reg.actividad_id),
                status='error',
                message='Registro no encontrado'
            ))
        except Exception as e:
            resultados.append(SyncResultOut(
                id=str(reg.actividad_id),
                status='error',
                message=str(e)
            ))

    return resultados


@router.post('/evidencias/upload')
def subir_evidencia(
    request,
    registro_id: UUID,
    tipo: str,
    latitud: Decimal,
    longitud: Decimal,
    fecha_captura: datetime,
    archivo: UploadedFile = File(...)
):
    """
    Upload a photo evidence.
    Triggers async processing for thumbnail and AI validation.
    """
    from apps.core.utils import upload_to_gcs
    from django.utils import timezone

    registro = RegistroCampo.objects.get(id=registro_id)

    # Generate unique filename
    import uuid
    extension = archivo.name.split('.')[-1] if '.' in archivo.name else 'jpg'
    filename = f"{uuid.uuid4()}.{extension}"
    path = f"evidencias/{registro_id}/{tipo}/{filename}"

    # Upload to cloud storage
    url = upload_to_gcs(archivo.read(), path)

    # Create evidence record
    evidencia = Evidencia.objects.create(
        registro_campo=registro,
        tipo=tipo,
        url_original=url,
        latitud=latitud,
        longitud=longitud,
        fecha_captura=fecha_captura,
    )

    # Trigger async processing (thumbnail, AI validation)
    procesar_evidencia.delay(str(evidencia.id))

    return {
        'id': str(evidencia.id),
        'url': url,
        'status': 'processing'
    }


@router.post('/registros/{registro_id}/firma')
def subir_firma(
    request,
    registro_id: UUID,
    archivo: UploadedFile = File(...)
):
    """Upload signature for a field record."""
    from apps.core.utils import upload_to_gcs

    registro = RegistroCampo.objects.get(id=registro_id)

    # Upload signature
    path = f"firmas/{registro_id}/firma.png"
    url = upload_to_gcs(archivo.read(), path)

    registro.firma_responsable_url = url
    registro.save(update_fields=['firma_responsable_url', 'updated_at'])

    return {'url': url}
