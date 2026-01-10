"""
API endpoints for transmission lines (Django Ninja).
"""
from ninja import Router, Schema
from typing import List, Optional
from uuid import UUID
from decimal import Decimal

from apps.api.auth import JWTAuth
from .models import Linea, Torre, PoligonoServidumbre

router = Router(auth=JWTAuth())


class LineaOut(Schema):
    id: UUID
    codigo: str
    nombre: str
    cliente: str
    tension_kv: Optional[int]
    longitud_km: Optional[Decimal]
    activa: bool


class TorreOut(Schema):
    id: UUID
    numero: str
    tipo: str
    estado: str
    latitud: Decimal
    longitud: Decimal
    altitud: Optional[Decimal]
    municipio: str
    linea_codigo: str
    linea_nombre: str


class TorreDetailOut(TorreOut):
    propietario_predio: str
    vereda: str
    altura_estructura: Optional[Decimal]
    observaciones: str
    tiene_poligono: bool


class PoligonoOut(Schema):
    id: UUID
    nombre: str
    area_hectareas: Optional[Decimal]
    ancho_franja: Optional[Decimal]
    # GeoJSON geometry
    geometria: dict


class ValidarUbicacionIn(Schema):
    latitud: Decimal
    longitud: Decimal
    torre_id: UUID


class ValidarUbicacionOut(Schema):
    dentro_poligono: bool
    torre_numero: str
    linea_codigo: str
    mensaje: str


@router.get('/lineas', response=List[LineaOut])
def listar_lineas(request, cliente: str = None, activa: bool = True):
    """List all transmission lines."""
    qs = Linea.objects.filter(activa=activa)
    if cliente:
        qs = qs.filter(cliente=cliente)
    return list(qs)


@router.get('/lineas/{linea_id}/torres', response=List[TorreOut])
def listar_torres_linea(request, linea_id: UUID):
    """List all towers for a specific line."""
    torres = Torre.objects.filter(linea_id=linea_id).select_related('linea')
    return [
        TorreOut(
            id=t.id,
            numero=t.numero,
            tipo=t.tipo,
            estado=t.estado,
            latitud=t.latitud,
            longitud=t.longitud,
            altitud=t.altitud,
            municipio=t.municipio,
            linea_codigo=t.linea.codigo,
            linea_nombre=t.linea.nombre,
        )
        for t in torres
    ]


@router.get('/torres/{torre_id}', response=TorreDetailOut)
def obtener_torre(request, torre_id: UUID):
    """Get tower details."""
    torre = Torre.objects.select_related('linea').get(id=torre_id)
    return TorreDetailOut(
        id=torre.id,
        numero=torre.numero,
        tipo=torre.tipo,
        estado=torre.estado,
        latitud=torre.latitud,
        longitud=torre.longitud,
        altitud=torre.altitud,
        municipio=torre.municipio,
        linea_codigo=torre.linea.codigo,
        linea_nombre=torre.linea.nombre,
        propietario_predio=torre.propietario_predio,
        vereda=torre.vereda,
        altura_estructura=torre.altura_estructura,
        observaciones=torre.observaciones,
        tiene_poligono=torre.poligonos.exists(),
    )


@router.get('/torres/{torre_id}/poligono', response=PoligonoOut)
def obtener_poligono_torre(request, torre_id: UUID):
    """Get easement polygon for a tower."""
    poligono = PoligonoServidumbre.objects.filter(torre_id=torre_id).first()
    if not poligono:
        return 404, {'detail': 'No hay polígono definido para esta torre'}

    # Convert geometry to GeoJSON
    import json
    geojson = json.loads(poligono.geometria.geojson)

    return PoligonoOut(
        id=poligono.id,
        nombre=poligono.nombre,
        area_hectareas=poligono.area_hectareas,
        ancho_franja=poligono.ancho_franja,
        geometria=geojson,
    )


@router.post('/validar-ubicacion', response=ValidarUbicacionOut)
def validar_ubicacion(request, data: ValidarUbicacionIn):
    """
    Validate if GPS coordinates are within the tower's easement polygon.
    Used by mobile app before allowing field data capture.
    """
    torre = Torre.objects.select_related('linea').get(id=data.torre_id)
    poligono = PoligonoServidumbre.objects.filter(torre=torre).first()

    if not poligono:
        # No polygon defined - allow but warn
        return ValidarUbicacionOut(
            dentro_poligono=True,
            torre_numero=torre.numero,
            linea_codigo=torre.linea.codigo,
            mensaje='No hay polígono de servidumbre definido. Ubicación aceptada.',
        )

    dentro = poligono.punto_dentro(float(data.latitud), float(data.longitud))

    if dentro:
        mensaje = 'Ubicación dentro del área de servidumbre autorizada.'
    else:
        mensaje = 'ADVERTENCIA: Ubicación fuera del área de servidumbre.'

    return ValidarUbicacionOut(
        dentro_poligono=dentro,
        torre_numero=torre.numero,
        linea_codigo=torre.linea.codigo,
        mensaje=mensaje,
    )
