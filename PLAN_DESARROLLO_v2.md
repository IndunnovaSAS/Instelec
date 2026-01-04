# Plan de Desarrollo v2.0 - Sistema TransMaint

## Sistema de Gestión Integral para Mantenimiento de Líneas de Transmisión

**Cliente:** Instelec Ingeniería S.A.S.
**Desarrollador:** Indunnova S.A.S.
**Versión:** 2.0
**Fecha:** Enero 2026

---

## 1. Stack Tecnológico Definitivo

### 1.1 Resumen de Tecnologías

| Capa | Tecnología | Versión |
|------|------------|---------|
| **Backend** | Python + Django | 3.12 / 5.1 LTS |
| **API Móvil** | Django Ninja | 1.x |
| **API Web** | Django REST Framework | 3.15+ |
| **Frontend Web** | HTMX + Alpine.js + Tailwind | 2.x / 3.x / 3.4 |
| **App Móvil** | Flutter | 3.x |
| **Base de Datos** | PostgreSQL + PostGIS | 17 |
| **Cache/Broker** | Redis | 7.x |
| **Tareas Async** | Celery + Beat | 5.3+ |
| **Almacenamiento** | Google Cloud Storage | - |
| **Despliegue** | Google Cloud Run | - |
| **CI/CD** | GitHub Actions | - |

---

## 2. Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              GOOGLE CLOUD PLATFORM                               │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                  │
│    ┌─────────────────┐         ┌─────────────────────────────────────────┐      │
│    │  Cloud Load     │         │            CLOUD RUN                    │      │
│    │  Balancing      │────────▶│                                         │      │
│    │  + Cloud CDN    │         │  ┌─────────────┐    ┌─────────────┐    │      │
│    └─────────────────┘         │  │   Django    │    │   Django    │    │      │
│                                │  │   Web App   │    │   API       │    │      │
│                                │  │   (HTMX)    │    │   (Ninja)   │    │      │
│                                │  │             │    │             │    │      │
│                                │  │  0-10 inst  │    │  0-10 inst  │    │      │
│                                │  └─────────────┘    └─────────────┘    │      │
│                                │                                         │      │
│                                └─────────────────────────────────────────┘      │
│                                              │                                   │
│           ┌──────────────────────────────────┼──────────────────────────────┐   │
│           │                                  │                              │   │
│           ▼                                  ▼                              ▼   │
│    ┌─────────────┐                  ┌─────────────┐                ┌───────────┐│
│    │ Cloud SQL   │                  │ Memorystore │                │  Cloud    ││
│    │ PostgreSQL  │                  │   Redis     │                │  Storage  ││
│    │   + PostGIS │                  │             │                │           ││
│    │             │                  │ • Cache     │                │ • Fotos   ││
│    │ • Datos     │                  │ • Sessions  │                │ • PDFs    ││
│    │ • Geometría │                  │ • Broker    │                │ • Excel   ││
│    └─────────────┘                  └─────────────┘                └───────────┘│
│                                              │                                   │
│                                              ▼                                   │
│                                     ┌─────────────────┐                         │
│                                     │   CLOUD RUN     │                         │
│                                     │   (Jobs)        │                         │
│                                     │                 │                         │
│                                     │ • Celery Worker │                         │
│                                     │ • Celery Beat   │                         │
│                                     │ • Report Gen    │                         │
│                                     └─────────────────┘                         │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                         │
                    ┌────────────────────┴────────────────────┐
                    │                                         │
                    ▼                                         ▼
          ┌─────────────────┐                      ┌─────────────────┐
          │   NAVEGADOR     │                      │   APP MÓVIL     │
          │                 │                      │   (Flutter)     │
          │ • Portal Web    │                      │                 │
          │ • HTMX          │                      │ • Android/iOS   │
          │ • Alpine.js     │                      │ • Offline Mode  │
          │ • Dashboards    │                      │ • GPS + Cámara  │
          │                 │                      │ • Sync Queue    │
          └─────────────────┘                      └─────────────────┘
```

---

## 3. Estructura del Proyecto

```
transmaint/
│
├── config/                          # Configuración Django
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                  # Configuración base
│   │   ├── local.py                 # Desarrollo local
│   │   ├── staging.py               # Ambiente de pruebas
│   │   └── production.py            # Producción (Cloud Run)
│   ├── urls.py                      # URLs principales
│   ├── celery.py                    # Configuración Celery
│   ├── asgi.py
│   └── wsgi.py
│
├── apps/                            # Aplicaciones Django
│   │
│   ├── core/                        # App base
│   │   ├── models.py                # BaseModel con timestamps
│   │   ├── mixins.py                # Mixins reutilizables
│   │   ├── utils.py                 # Utilidades generales
│   │   └── management/
│   │       └── commands/            # Comandos personalizados
│   │
│   ├── usuarios/                    # Gestión de usuarios
│   │   ├── models.py                # User, Rol, Permiso
│   │   ├── views.py                 # Login, perfil
│   │   ├── api.py                   # API endpoints (Ninja)
│   │   ├── forms.py
│   │   ├── admin.py
│   │   └── templates/usuarios/
│   │
│   ├── lineas/                      # Líneas y torres
│   │   ├── models.py                # Linea, Torre, PoligonoServidumbre
│   │   ├── views.py                 # CRUD con HTMX
│   │   ├── api.py                   # API para móvil
│   │   ├── admin.py                 # GeoDjango admin
│   │   └── templates/lineas/
│   │
│   ├── cuadrillas/                  # Gestión de cuadrillas
│   │   ├── models.py                # Cuadrilla, Miembro, Vehiculo
│   │   ├── views.py
│   │   ├── api.py
│   │   └── templates/cuadrillas/
│   │
│   ├── actividades/                 # Programación
│   │   ├── models.py                # Actividad, TipoActividad
│   │   ├── views.py                 # Calendario, Gantt
│   │   ├── api.py
│   │   ├── services.py              # Lógica de programación
│   │   └── templates/actividades/
│   │
│   ├── campo/                       # Captura en campo
│   │   ├── models.py                # RegistroCampo, Evidencia
│   │   ├── views.py                 # Visualización de registros
│   │   ├── api.py                   # API sync móvil
│   │   ├── validators.py            # Validación GPS, fotos
│   │   ├── tasks.py                 # Celery tasks
│   │   └── templates/campo/
│   │
│   ├── ambiental/                   # Gestión ambiental
│   │   ├── models.py                # InformeAmbiental, PermisoServidumbre
│   │   ├── views.py                 # Consolidación, reportes
│   │   ├── reports.py               # Generación PDF/Excel
│   │   ├── tasks.py                 # Generación async
│   │   └── templates/ambiental/
│   │
│   ├── financiero/                  # Control financiero
│   │   ├── models.py                # Presupuesto, CostoRecurso
│   │   ├── views.py                 # Dashboard financiero
│   │   ├── reports.py               # Cuadro de costos
│   │   └── templates/financiero/
│   │
│   ├── indicadores/                 # KPIs y ANS
│   │   ├── models.py                # Indicador, MetaANS
│   │   ├── views.py                 # Dashboard ejecutivo
│   │   ├── calculators.py           # Cálculo de métricas
│   │   └── templates/indicadores/
│   │
│   └── api/                         # API unificada (Django Ninja)
│       ├── __init__.py
│       ├── router.py                # Router principal
│       ├── schemas.py               # Pydantic schemas
│       ├── auth.py                  # JWT authentication
│       └── exceptions.py            # Manejo de errores
│
├── templates/                       # Templates globales
│   ├── base.html                    # Layout principal
│   ├── components/                  # Componentes HTMX
│   │   ├── navbar.html
│   │   ├── sidebar.html
│   │   ├── modal.html
│   │   ├── table.html
│   │   ├── pagination.html
│   │   ├── alerts.html
│   │   └── loading.html
│   ├── partials/                    # Fragmentos HTMX
│   └── errors/
│       ├── 404.html
│       └── 500.html
│
├── static/                          # Archivos estáticos
│   ├── css/
│   │   └── app.css                  # Tailwind compilado
│   ├── js/
│   │   ├── app.js                   # Alpine.js components
│   │   └── charts.js                # ECharts config
│   └── img/
│
├── mobile/                          # App Flutter
│   ├── lib/
│   │   ├── main.dart
│   │   ├── app/
│   │   │   ├── app.dart
│   │   │   └── routes.dart
│   │   ├── core/
│   │   │   ├── api/
│   │   │   │   ├── api_client.dart
│   │   │   │   └── interceptors.dart
│   │   │   ├── database/
│   │   │   │   ├── database.dart
│   │   │   │   └── daos/
│   │   │   ├── sync/
│   │   │   │   ├── sync_manager.dart
│   │   │   │   └── sync_queue.dart
│   │   │   └── services/
│   │   │       ├── location_service.dart
│   │   │       ├── camera_service.dart
│   │   │       └── photo_validator.dart
│   │   ├── features/
│   │   │   ├── auth/
│   │   │   │   ├── data/
│   │   │   │   ├── domain/
│   │   │   │   └── presentation/
│   │   │   ├── actividades/
│   │   │   │   ├── data/
│   │   │   │   ├── domain/
│   │   │   │   └── presentation/
│   │   │   ├── captura/
│   │   │   │   ├── data/
│   │   │   │   ├── domain/
│   │   │   │   └── presentation/
│   │   │   │       ├── screens/
│   │   │   │       ├── widgets/
│   │   │   │       └── bloc/
│   │   │   └── sync/
│   │   └── shared/
│   │       ├── widgets/
│   │       └── utils/
│   ├── assets/
│   │   └── ml/
│   │       └── photo_validator.tflite
│   ├── android/
│   ├── ios/
│   └── pubspec.yaml
│
├── infrastructure/                  # Infraestructura
│   ├── docker/
│   │   ├── Dockerfile               # Django app
│   │   ├── Dockerfile.celery        # Celery worker
│   │   └── docker-compose.yml       # Desarrollo local
│   ├── cloudbuild/
│   │   ├── cloudbuild.yaml          # CI/CD Cloud Build
│   │   └── cloudbuild-mobile.yaml   # Build Flutter
│   ├── terraform/                   # IaC
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   ├── cloud_run.tf
│   │   ├── cloud_sql.tf
│   │   ├── memorystore.tf
│   │   └── storage.tf
│   └── scripts/
│       ├── deploy.sh
│       ├── migrate.sh
│       └── seed_data.sh
│
├── docs/                            # Documentación
│   ├── mkdocs.yml
│   └── docs/
│       ├── index.md
│       ├── arquitectura.md
│       ├── api.md
│       ├── despliegue.md
│       └── usuario/
│
├── tests/                           # Tests
│   ├── conftest.py                  # Fixtures pytest
│   ├── factories/                   # Factory Boy
│   │   ├── usuarios.py
│   │   ├── lineas.py
│   │   └── actividades.py
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── requirements/
│   ├── base.txt
│   ├── local.txt
│   └── production.txt
│
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── deploy.yml
│
├── .pre-commit-config.yaml
├── pyproject.toml
├── pytest.ini
├── manage.py
└── README.md
```

---

## 4. Modelo de Datos

### 4.1 Diagrama Entidad-Relación

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                            MODELO DE DATOS                                       │
└─────────────────────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Usuario    │         │   Cuadrilla  │         │   Vehiculo   │
├──────────────┤         ├──────────────┤         ├──────────────┤
│ id (UUID)    │◄────────│ supervisor   │         │ id (UUID)    │
│ email        │         │ id (UUID)    │◄────────│ placa        │
│ nombre       │         │ codigo       │         │ tipo         │
│ telefono     │         │ nombre       │─────────│ costo_dia    │
│ rol          │         │ vehiculo ────┼────────▶│ activo       │
│ activo       │         │ activa       │         └──────────────┘
└──────────────┘         └──────────────┘
       │                        │
       │                        │
       ▼                        ▼
┌──────────────┐         ┌──────────────┐
│  Cuadrilla   │         │  Actividad   │         ┌──────────────┐
│  Miembro     │         ├──────────────┤         │    Linea     │
├──────────────┤         │ id (UUID)    │         ├──────────────┤
│ cuadrilla    │         │ linea ───────┼────────▶│ id (UUID)    │
│ usuario      │         │ torre ───────┼────┐    │ codigo       │
│ rol_cuadrill │         │ tipo_activ   │    │    │ nombre       │
│ activo       │         │ cuadrilla    │    │    │ cliente      │
└──────────────┘         │ fecha_prog   │    │    │ tension_kv   │
                         │ estado       │    │    └──────────────┘
                         │ prioridad    │    │           │
                         └──────────────┘    │           │
                                │            │           ▼
                                │            │    ┌──────────────┐
                                ▼            │    │    Torre     │
                         ┌──────────────┐    │    ├──────────────┤
                         │  Registro    │    └───▶│ id (UUID)    │
                         │   Campo      │         │ linea        │
                         ├──────────────┤         │ numero       │
                         │ id (UUID)    │         │ tipo         │
                         │ actividad    │         │ latitud      │
                         │ usuario      │         │ longitud     │
                         │ fecha_inicio │         │ geometria    │
                         │ lat/long     │         └──────────────┘
                         │ dentro_polig │                │
                         │ datos_form   │                │
                         │ sincronizado │                ▼
                         └──────────────┘         ┌──────────────┐
                                │                 │  Poligono    │
                                │                 │ Servidumbre  │
                                ▼                 ├──────────────┤
                         ┌──────────────┐         │ torre        │
                         │  Evidencia   │         │ geometria    │
                         ├──────────────┤         │ area_ha      │
                         │ id (UUID)    │         └──────────────┘
                         │ registro     │
                         │ tipo (A/D/D) │
                         │ url          │
                         │ lat/long     │
                         │ validacion_ia│
                         └──────────────┘
```

### 4.2 Modelos Django

```python
# apps/core/models.py
import uuid
from django.db import models

class BaseModel(models.Model):
    """Modelo base con campos comunes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# apps/usuarios/models.py
from django.contrib.auth.models import AbstractUser
from apps.core.models import BaseModel

class Usuario(AbstractUser, BaseModel):
    class Rol(models.TextChoices):
        ADMIN = 'admin', 'Administrador'
        DIRECTOR = 'director', 'Director de Proyecto'
        COORDINADOR = 'coordinador', 'Coordinador'
        ING_RESIDENTE = 'ing_residente', 'Ingeniero Residente'
        ING_AMBIENTAL = 'ing_ambiental', 'Ingeniero Ambiental'
        SUPERVISOR = 'supervisor', 'Supervisor de Cuadrilla'
        LINIERO = 'liniero', 'Liniero'
        AUXILIAR = 'auxiliar', 'Auxiliar'

    telefono = models.CharField(max_length=20, blank=True)
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.LINIERO)

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'


# apps/lineas/models.py
from django.contrib.gis.db import models as gis_models
from apps.core.models import BaseModel

class Linea(BaseModel):
    class Cliente(models.TextChoices):
        TRANSELCA = 'TRANSELCA', 'Transelca'
        INTERCOLOMBIA = 'INTERCOLOMBIA', 'Intercolombia'

    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    cliente = models.CharField(max_length=20, choices=Cliente.choices)
    longitud_km = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    tension_kv = models.PositiveIntegerField(null=True)
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = 'lineas'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Torre(BaseModel):
    class TipoTorre(models.TextChoices):
        SUSPENSION = 'SUSPENSION', 'Suspensión'
        ANCLAJE = 'ANCLAJE', 'Anclaje'
        TERMINAL = 'TERMINAL', 'Terminal'

    linea = models.ForeignKey(Linea, on_delete=models.CASCADE, related_name='torres')
    numero = models.CharField(max_length=20)
    tipo = models.CharField(max_length=20, choices=TipoTorre.choices, null=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=8)
    longitud = models.DecimalField(max_digits=11, decimal_places=8)
    altitud = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    geometria = gis_models.PointField(srid=4326, null=True)

    class Meta:
        db_table = 'torres'
        unique_together = ['linea', 'numero']
        ordering = ['linea', 'numero']

    def save(self, *args, **kwargs):
        from django.contrib.gis.geos import Point
        if self.latitud and self.longitud:
            self.geometria = Point(float(self.longitud), float(self.latitud), srid=4326)
        super().save(*args, **kwargs)


class PoligonoServidumbre(BaseModel):
    linea = models.ForeignKey(Linea, on_delete=models.CASCADE, null=True)
    torre = models.ForeignKey(Torre, on_delete=models.CASCADE, null=True)
    nombre = models.CharField(max_length=100, blank=True)
    geometria = gis_models.PolygonField(srid=4326)
    area_hectareas = models.DecimalField(max_digits=10, decimal_places=4, null=True)

    class Meta:
        db_table = 'poligonos_servidumbre'

    def punto_dentro(self, lat: float, lon: float) -> bool:
        """Verifica si un punto está dentro del polígono"""
        from django.contrib.gis.geos import Point
        punto = Point(lon, lat, srid=4326)
        return self.geometria.contains(punto)


# apps/actividades/models.py
class TipoActividad(BaseModel):
    class Categoria(models.TextChoices):
        PODA = 'PODA', 'Poda de Vegetación'
        HERRAJES = 'HERRAJES', 'Cambio de Herrajes'
        INSPECCION = 'INSPECCION', 'Inspección'
        LIMPIEZA = 'LIMPIEZA', 'Limpieza'
        OTRO = 'OTRO', 'Otro'

    codigo = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=Categoria.choices)
    requiere_fotos_antes = models.BooleanField(default=True)
    requiere_fotos_durante = models.BooleanField(default=True)
    requiere_fotos_despues = models.BooleanField(default=True)
    campos_formulario = models.JSONField(default=dict, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'tipos_actividad'


class Actividad(BaseModel):
    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        EN_CURSO = 'EN_CURSO', 'En Curso'
        COMPLETADA = 'COMPLETADA', 'Completada'
        CANCELADA = 'CANCELADA', 'Cancelada'

    class Prioridad(models.TextChoices):
        BAJA = 'BAJA', 'Baja'
        NORMAL = 'NORMAL', 'Normal'
        ALTA = 'ALTA', 'Alta'
        URGENTE = 'URGENTE', 'Urgente'

    linea = models.ForeignKey('lineas.Linea', on_delete=models.CASCADE)
    torre = models.ForeignKey('lineas.Torre', on_delete=models.CASCADE)
    tipo_actividad = models.ForeignKey(TipoActividad, on_delete=models.PROTECT)
    cuadrilla = models.ForeignKey('cuadrillas.Cuadrilla', on_delete=models.SET_NULL, null=True)
    fecha_programada = models.DateField()
    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    prioridad = models.CharField(max_length=10, choices=Prioridad.choices, default=Prioridad.NORMAL)
    observaciones_programacion = models.TextField(blank=True)

    class Meta:
        db_table = 'actividades'
        ordering = ['-fecha_programada', 'prioridad']


# apps/campo/models.py
class RegistroCampo(BaseModel):
    actividad = models.ForeignKey('actividades.Actividad', on_delete=models.CASCADE)
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.PROTECT)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField(null=True)
    latitud_inicio = models.DecimalField(max_digits=10, decimal_places=8, null=True)
    longitud_inicio = models.DecimalField(max_digits=11, decimal_places=8, null=True)
    latitud_fin = models.DecimalField(max_digits=10, decimal_places=8, null=True)
    longitud_fin = models.DecimalField(max_digits=11, decimal_places=8, null=True)
    dentro_poligono = models.BooleanField(null=True)
    datos_formulario = models.JSONField(default=dict)
    observaciones = models.TextField(blank=True)
    observaciones_audio_url = models.URLField(blank=True)
    firma_responsable_url = models.URLField(blank=True)
    sincronizado = models.BooleanField(default=False)

    class Meta:
        db_table = 'registros_campo'


class Evidencia(BaseModel):
    class TipoEvidencia(models.TextChoices):
        ANTES = 'ANTES', 'Antes'
        DURANTE = 'DURANTE', 'Durante'
        DESPUES = 'DESPUES', 'Después'

    registro_campo = models.ForeignKey(RegistroCampo, on_delete=models.CASCADE, related_name='evidencias')
    tipo = models.CharField(max_length=10, choices=TipoEvidencia.choices)
    url_original = models.URLField()
    url_thumbnail = models.URLField(blank=True)
    latitud = models.DecimalField(max_digits=10, decimal_places=8, null=True)
    longitud = models.DecimalField(max_digits=11, decimal_places=8, null=True)
    fecha_captura = models.DateTimeField()
    validacion_ia = models.JSONField(default=dict)  # {nitidez, iluminacion, valida}
    metadata_exif = models.JSONField(default=dict)

    class Meta:
        db_table = 'evidencias'
        ordering = ['tipo', 'fecha_captura']
```

---

## 5. API para App Móvil (Django Ninja)

### 5.1 Configuración

```python
# apps/api/router.py
from ninja import NinjaAPI
from ninja.security import HttpBearer
from apps.api.auth import JWTAuth

api = NinjaAPI(
    title="TransMaint API",
    version="1.0.0",
    description="API para app móvil de captura en campo",
    auth=JWTAuth(),
)

# Registrar routers
from apps.usuarios.api import router as usuarios_router
from apps.actividades.api import router as actividades_router
from apps.campo.api import router as campo_router
from apps.lineas.api import router as lineas_router

api.add_router("/auth/", usuarios_router, tags=["Autenticación"])
api.add_router("/actividades/", actividades_router, tags=["Actividades"])
api.add_router("/campo/", campo_router, tags=["Campo"])
api.add_router("/lineas/", lineas_router, tags=["Líneas"])
```

### 5.2 Endpoints Principales

```python
# apps/actividades/api.py
from ninja import Router, Schema
from typing import List
from datetime import date
from uuid import UUID

router = Router()

class ActividadOut(Schema):
    id: UUID
    linea_codigo: str
    linea_nombre: str
    torre_numero: str
    torre_latitud: float
    torre_longitud: float
    tipo_actividad_nombre: str
    tipo_actividad_categoria: str
    fecha_programada: date
    estado: str
    prioridad: str
    campos_formulario: dict

@router.get("/mis-actividades", response=List[ActividadOut])
def listar_mis_actividades(request, fecha: date = None):
    """Lista actividades asignadas al usuario autenticado"""
    cuadrilla = request.user.cuadrilla_actual
    qs = Actividad.objects.filter(
        cuadrilla=cuadrilla,
        estado__in=['PENDIENTE', 'EN_CURSO']
    ).select_related('linea', 'torre', 'tipo_actividad')

    if fecha:
        qs = qs.filter(fecha_programada=fecha)

    return qs

@router.post("/{actividad_id}/iniciar")
def iniciar_actividad(request, actividad_id: UUID, lat: float, lon: float):
    """Marca una actividad como iniciada"""
    actividad = get_object_or_404(Actividad, id=actividad_id)
    actividad.estado = 'EN_CURSO'
    actividad.save()

    # Crear registro de campo
    registro = RegistroCampo.objects.create(
        actividad=actividad,
        usuario=request.user,
        fecha_inicio=timezone.now(),
        latitud_inicio=lat,
        longitud_inicio=lon,
        dentro_poligono=validar_ubicacion(actividad.torre, lat, lon)
    )

    return {"registro_id": registro.id, "dentro_poligono": registro.dentro_poligono}


# apps/campo/api.py
from ninja import Router, File, UploadedFile
from apps.campo.tasks import procesar_evidencia

router = Router()

class RegistroIn(Schema):
    actividad_id: UUID
    datos_formulario: dict
    observaciones: str = ""
    latitud_fin: float
    longitud_fin: float
    fecha_fin: datetime

@router.post("/registros/sync")
def sincronizar_registros(request, registros: List[RegistroIn]):
    """Sincroniza múltiples registros desde la app móvil"""
    resultados = []

    for reg in registros:
        try:
            registro = RegistroCampo.objects.get(actividad_id=reg.actividad_id)
            registro.datos_formulario = reg.datos_formulario
            registro.observaciones = reg.observaciones
            registro.latitud_fin = reg.latitud_fin
            registro.longitud_fin = reg.longitud_fin
            registro.fecha_fin = reg.fecha_fin
            registro.sincronizado = True
            registro.save()

            # Marcar actividad como completada
            registro.actividad.estado = 'COMPLETADA'
            registro.actividad.save()

            resultados.append({"id": str(reg.actividad_id), "status": "ok"})
        except Exception as e:
            resultados.append({"id": str(reg.actividad_id), "status": "error", "message": str(e)})

    return {"resultados": resultados}

@router.post("/evidencias/upload")
def subir_evidencia(
    request,
    registro_id: UUID,
    tipo: str,
    lat: float,
    lon: float,
    fecha_captura: datetime,
    archivo: UploadedFile = File(...)
):
    """Sube una evidencia fotográfica"""
    registro = get_object_or_404(RegistroCampo, id=registro_id)

    # Subir a Cloud Storage
    url = upload_to_gcs(archivo, f"evidencias/{registro_id}/{tipo}/")

    evidencia = Evidencia.objects.create(
        registro_campo=registro,
        tipo=tipo,
        url_original=url,
        latitud=lat,
        longitud=lon,
        fecha_captura=fecha_captura,
    )

    # Procesar en background (thumbnail, validación IA)
    procesar_evidencia.delay(str(evidencia.id))

    return {"id": evidencia.id, "url": url}
```

---

## 6. Frontend Web (HTMX + Alpine.js)

### 6.1 Template Base

```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="es" x-data="{ sidebarOpen: true, darkMode: false }" :class="{ 'dark': darkMode }">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}TransMaint{% endblock %}</title>

    <!-- Tailwind CSS -->
    <link href="{% static 'css/app.css' %}" rel="stylesheet">

    <!-- HTMX -->
    <script src="https://unpkg.com/htmx.org@2.0.0"></script>
    <script src="https://unpkg.com/htmx.org@2.0.0/dist/ext/loading-states.js"></script>

    <!-- Alpine.js -->
    <script defer src="https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js"></script>

    <!-- ECharts (solo en páginas con gráficos) -->
    {% block extra_head %}{% endblock %}
</head>
<body class="bg-gray-100 dark:bg-gray-900" hx-ext="loading-states">

    <div class="flex h-screen overflow-hidden">
        <!-- Sidebar -->
        {% include "components/sidebar.html" %}

        <!-- Main Content -->
        <div class="flex-1 flex flex-col overflow-hidden">
            <!-- Navbar -->
            {% include "components/navbar.html" %}

            <!-- Page Content -->
            <main class="flex-1 overflow-y-auto p-6">
                {% block content %}{% endblock %}
            </main>
        </div>
    </div>

    <!-- Toast Notifications -->
    <div id="toast-container" class="fixed top-4 right-4 z-50 space-y-2"></div>

    <!-- Modal Container -->
    <div id="modal-container"></div>

    {% block extra_js %}{% endblock %}
</body>
</html>
```

### 6.2 Componentes HTMX

```html
<!-- templates/actividades/partials/lista_actividades.html -->
<div id="actividades-list" class="space-y-4">
    {% for actividad in actividades %}
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-4 hover:shadow-md transition"
         x-data="{ expanded: false }">

        <div class="flex items-center justify-between">
            <div class="flex items-center space-x-4">
                <!-- Estado -->
                <span class="flex-shrink-0">
                    {% if actividad.estado == 'COMPLETADA' %}
                        <span class="w-3 h-3 bg-green-500 rounded-full inline-block"></span>
                    {% elif actividad.estado == 'EN_CURSO' %}
                        <span class="w-3 h-3 bg-yellow-500 rounded-full inline-block animate-pulse"></span>
                    {% else %}
                        <span class="w-3 h-3 bg-gray-300 rounded-full inline-block"></span>
                    {% endif %}
                </span>

                <!-- Info -->
                <div>
                    <h3 class="font-medium text-gray-900 dark:text-white">
                        Torre {{ actividad.torre.numero }} - {{ actividad.linea.codigo }}
                    </h3>
                    <p class="text-sm text-gray-500">
                        {{ actividad.tipo_actividad.nombre }} • {{ actividad.fecha_programada|date:"d M Y" }}
                    </p>
                </div>
            </div>

            <!-- Actions -->
            <div class="flex items-center space-x-2">
                <span class="px-2 py-1 text-xs rounded-full
                    {% if actividad.prioridad == 'URGENTE' %}bg-red-100 text-red-800
                    {% elif actividad.prioridad == 'ALTA' %}bg-orange-100 text-orange-800
                    {% else %}bg-gray-100 text-gray-800{% endif %}">
                    {{ actividad.get_prioridad_display }}
                </span>

                <button @click="expanded = !expanded" class="p-2 hover:bg-gray-100 rounded">
                    <svg class="w-5 h-5 transition-transform" :class="{ 'rotate-180': expanded }"
                         fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"/>
                    </svg>
                </button>
            </div>
        </div>

        <!-- Detalles expandibles -->
        <div x-show="expanded" x-collapse class="mt-4 pt-4 border-t">
            <div hx-get="{% url 'actividades:detalle_partial' actividad.id %}"
                 hx-trigger="revealed"
                 hx-swap="innerHTML">
                <div class="flex justify-center py-4">
                    <svg class="animate-spin h-6 w-6 text-blue-500" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"/>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                    </svg>
                </div>
            </div>
        </div>
    </div>
    {% empty %}
    <div class="text-center py-12 text-gray-500">
        No hay actividades programadas
    </div>
    {% endfor %}
</div>

<!-- Paginación HTMX -->
{% if page_obj.has_next %}
<div hx-get="?page={{ page_obj.next_page_number }}"
     hx-trigger="revealed"
     hx-swap="afterend"
     hx-select="#actividades-list > *"
     class="flex justify-center py-4">
    <span class="text-gray-500">Cargando más...</span>
</div>
{% endif %}
```

### 6.3 Dashboard con ECharts

```html
<!-- templates/indicadores/dashboard.html -->
{% extends "base.html" %}

{% block extra_head %}
<script src="https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"></script>
{% endblock %}

{% block content %}
<div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center">
        <h1 class="text-2xl font-bold text-gray-900 dark:text-white">Dashboard de Indicadores</h1>
        <div class="flex space-x-2">
            <select x-data x-model="mes" @change="htmx.trigger('#dashboard', 'refresh')"
                    class="rounded-md border-gray-300">
                {% for m in meses %}
                <option value="{{ m.value }}" {% if m.value == mes_actual %}selected{% endif %}>
                    {{ m.label }}
                </option>
                {% endfor %}
            </select>
        </div>
    </div>

    <!-- KPIs Cards -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {% include "indicadores/partials/kpi_card.html" with titulo="Cumplimiento" valor=kpis.cumplimiento meta=95 %}
        {% include "indicadores/partials/kpi_card.html" with titulo="Actividades" valor=kpis.actividades_completadas formato="numero" %}
        {% include "indicadores/partials/kpi_card.html" with titulo="Días sin Accidentes" valor=kpis.dias_sin_accidentes formato="numero" %}
        {% include "indicadores/partials/kpi_card.html" with titulo="Informes a Tiempo" valor=kpis.informes_tiempo meta=95 %}
    </div>

    <!-- Charts -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Cumplimiento por Cuadrilla -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 class="text-lg font-medium mb-4">Cumplimiento por Cuadrilla</h3>
            <div id="chart-cuadrillas" class="h-80"
                 x-data
                 x-init="
                    const chart = echarts.init($el);
                    chart.setOption({
                        tooltip: { trigger: 'axis' },
                        xAxis: { type: 'category', data: {{ cuadrillas_labels|safe }} },
                        yAxis: { type: 'value', max: 100 },
                        series: [{
                            type: 'bar',
                            data: {{ cuadrillas_data|safe }},
                            itemStyle: {
                                color: function(params) {
                                    return params.value >= 90 ? '#10B981' :
                                           params.value >= 75 ? '#F59E0B' : '#EF4444';
                                }
                            }
                        }]
                    });
                    window.addEventListener('resize', () => chart.resize());
                 ">
            </div>
        </div>

        <!-- Tendencia Mensual -->
        <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h3 class="text-lg font-medium mb-4">Tendencia de Cumplimiento</h3>
            <div id="chart-tendencia" class="h-80"
                 x-data
                 x-init="
                    const chart = echarts.init($el);
                    chart.setOption({
                        tooltip: { trigger: 'axis' },
                        legend: { data: ['Planeado', 'Ejecutado'] },
                        xAxis: { type: 'category', data: {{ meses_labels|safe }} },
                        yAxis: { type: 'value' },
                        series: [
                            { name: 'Planeado', type: 'line', data: {{ planeado_data|safe }} },
                            { name: 'Ejecutado', type: 'line', data: {{ ejecutado_data|safe }} }
                        ]
                    });
                    window.addEventListener('resize', () => chart.resize());
                 ">
            </div>
        </div>
    </div>

    <!-- Mapa de Cuadrillas en Tiempo Real -->
    <div class="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
        <h3 class="text-lg font-medium mb-4">Ubicación de Cuadrillas</h3>
        <div id="mapa-cuadrillas" class="h-96 rounded-lg overflow-hidden"
             hx-get="{% url 'cuadrillas:mapa_partial' %}"
             hx-trigger="load, every 30s"
             hx-swap="innerHTML">
        </div>
    </div>
</div>
{% endblock %}
```

---

## 7. Tareas Asíncronas (Celery)

### 7.1 Configuración

```python
# config/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

app = Celery('transmaint')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Configuración de colas
app.conf.task_queues = {
    'high_priority': {'exchange': 'high', 'routing_key': 'high'},
    'default': {'exchange': 'default', 'routing_key': 'default'},
    'reports': {'exchange': 'reports', 'routing_key': 'reports'},
}

app.conf.task_routes = {
    'apps.campo.tasks.*': {'queue': 'high_priority'},
    'apps.ambiental.tasks.*': {'queue': 'reports'},
    'apps.financiero.tasks.*': {'queue': 'reports'},
}
```

### 7.2 Tasks Principales

```python
# apps/campo/tasks.py
from celery import shared_task
from PIL import Image
import io

@shared_task(bind=True, max_retries=3)
def procesar_evidencia(self, evidencia_id: str):
    """Procesa una evidencia: thumbnail y validación IA"""
    from apps.campo.models import Evidencia
    from apps.campo.services import PhotoValidator, upload_to_gcs

    try:
        evidencia = Evidencia.objects.get(id=evidencia_id)

        # Descargar imagen original
        imagen = download_from_gcs(evidencia.url_original)

        # Generar thumbnail
        thumb = Image.open(io.BytesIO(imagen))
        thumb.thumbnail((400, 400))
        thumb_bytes = io.BytesIO()
        thumb.save(thumb_bytes, format='JPEG', quality=85)

        thumb_url = upload_to_gcs(
            thumb_bytes.getvalue(),
            f"evidencias/{evidencia.registro_campo_id}/thumbs/{evidencia.id}.jpg"
        )

        # Validar con IA
        validator = PhotoValidator()
        validacion = validator.validate(imagen)

        # Actualizar evidencia
        evidencia.url_thumbnail = thumb_url
        evidencia.validacion_ia = validacion
        evidencia.save()

        return {"status": "ok", "validacion": validacion}

    except Exception as e:
        self.retry(exc=e, countdown=60)


# apps/ambiental/tasks.py
from celery import shared_task
from weasyprint import HTML

@shared_task
def generar_informe_ambiental(informe_id: str):
    """Genera PDF del informe ambiental mensual"""
    from apps.ambiental.models import InformeAmbiental
    from apps.ambiental.reports import InformeAmbientalGenerator

    informe = InformeAmbiental.objects.get(id=informe_id)

    # Consolidar datos
    generator = InformeAmbientalGenerator(informe)
    html_content = generator.render_html()

    # Generar PDF
    pdf = HTML(string=html_content).write_pdf()

    # Subir a Cloud Storage
    url = upload_to_gcs(
        pdf,
        f"informes/ambiental/{informe.periodo_anio}/{informe.periodo_mes}/{informe.linea.codigo}.pdf"
    )

    informe.url_pdf = url
    informe.estado = 'GENERADO'
    informe.save()

    return {"url": url}


@shared_task
def generar_cuadro_costos(anio: int, mes: int, linea_id: str):
    """Genera Excel del cuadro de costos para facturación"""
    from apps.financiero.reports import CuadroCostosGenerator
    import openpyxl

    generator = CuadroCostosGenerator(anio, mes, linea_id)
    workbook = generator.generate()

    # Guardar en buffer
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    # Subir a Cloud Storage
    url = upload_to_gcs(
        buffer.getvalue(),
        f"informes/costos/{anio}/{mes}/cuadro_costos_{linea_id}.xlsx"
    )

    return {"url": url}
```

---

## 8. Infraestructura Google Cloud

### 8.1 Terraform

```hcl
# infrastructure/terraform/main.tf

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
  backend "gcs" {
    bucket = "transmaint-terraform-state"
    prefix = "terraform/state"
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Variables
variable "project_id" {
  default = "transmaint-prod"
}

variable "region" {
  default = "us-central1"
}

# Cloud SQL (PostgreSQL + PostGIS)
resource "google_sql_database_instance" "main" {
  name             = "transmaint-db"
  database_version = "POSTGRES_17"
  region           = var.region

  settings {
    tier = "db-custom-2-4096"  # 2 vCPU, 4GB RAM

    database_flags {
      name  = "max_connections"
      value = "100"
    }

    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      point_in_time_recovery_enabled = true
      backup_retention_settings {
        retained_backups = 7
      }
    }

    ip_configuration {
      ipv4_enabled = false
      private_network = google_compute_network.vpc.id
    }
  }

  deletion_protection = true
}

resource "google_sql_database" "transmaint" {
  name     = "transmaint"
  instance = google_sql_database_instance.main.name
}

# Memorystore (Redis)
resource "google_redis_instance" "cache" {
  name           = "transmaint-redis"
  tier           = "BASIC"
  memory_size_gb = 1
  region         = var.region

  authorized_network = google_compute_network.vpc.id

  redis_version = "REDIS_7_0"
}

# Cloud Storage
resource "google_storage_bucket" "media" {
  name     = "transmaint-media-${var.project_id}"
  location = var.region

  uniform_bucket_level_access = true

  lifecycle_rule {
    condition {
      age = 365
    }
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
  }

  cors {
    origin          = ["https://transmaint.instelec.com.co"]
    method          = ["GET", "HEAD", "PUT", "POST"]
    response_header = ["*"]
    max_age_seconds = 3600
  }
}

# Cloud Run - Web App
resource "google_cloud_run_v2_service" "web" {
  name     = "transmaint-web"
  location = var.region

  template {
    containers {
      image = "gcr.io/${var.project_id}/transmaint-web:latest"

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }

      env {
        name  = "DJANGO_SETTINGS_MODULE"
        value = "config.settings.production"
      }

      env {
        name = "DATABASE_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.db_url.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "REDIS_URL"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.redis_url.secret_id
            version = "latest"
          }
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "PRIVATE_RANGES_ONLY"
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }
}

# Cloud Run - Celery Worker
resource "google_cloud_run_v2_service" "celery" {
  name     = "transmaint-celery"
  location = var.region

  template {
    containers {
      image   = "gcr.io/${var.project_id}/transmaint-celery:latest"
      command = ["celery", "-A", "config", "worker", "-l", "info", "-Q", "default,high_priority"]

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }
    }

    scaling {
      min_instance_count = 1
      max_instance_count = 5
    }
  }
}

# Cloud Run - Celery Beat
resource "google_cloud_run_v2_job" "celery_beat" {
  name     = "transmaint-celery-beat"
  location = var.region

  template {
    template {
      containers {
        image   = "gcr.io/${var.project_id}/transmaint-celery:latest"
        command = ["celery", "-A", "config", "beat", "-l", "info"]
      }
    }
  }
}

# VPC y conectores
resource "google_compute_network" "vpc" {
  name                    = "transmaint-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "transmaint-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.vpc.id
}

resource "google_vpc_access_connector" "connector" {
  name          = "transmaint-connector"
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.vpc.name
}

# Secrets
resource "google_secret_manager_secret" "db_url" {
  secret_id = "transmaint-db-url"

  replication {
    auto {}
  }
}

resource "google_secret_manager_secret" "redis_url" {
  secret_id = "transmaint-redis-url"

  replication {
    auto {}
  }
}

# Outputs
output "web_url" {
  value = google_cloud_run_v2_service.web.uri
}

output "db_connection" {
  value     = google_sql_database_instance.main.connection_name
  sensitive = true
}
```

### 8.2 Dockerfile

```dockerfile
# infrastructure/docker/Dockerfile
FROM python:3.12-slim

# Variables de entorno
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Instalar dependencias del sistema (incluyendo GDAL para GeoDjango)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gdal-bin \
    libgdal-dev \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no-root
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Instalar dependencias Python
COPY requirements/production.txt requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copiar código
COPY --chown=appuser:appuser . .

# Recolectar archivos estáticos
RUN python manage.py collectstatic --noinput

USER appuser

# Puerto
EXPOSE 8080

# Comando de inicio
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4"]
```

### 8.3 Docker Compose (Desarrollo Local)

```yaml
# infrastructure/docker/docker-compose.yml
version: '3.8'

services:
  web:
    build:
      context: ../..
      dockerfile: infrastructure/docker/Dockerfile
    ports:
      - "8000:8080"
    volumes:
      - ../..:/app
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.local
      - DATABASE_URL=postgis://postgres:postgres@db:5432/transmaint
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis
    command: python manage.py runserver 0.0.0.0:8080

  db:
    image: postgis/postgis:17-3.4
    environment:
      POSTGRES_DB: transmaint
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery:
    build:
      context: ../..
      dockerfile: infrastructure/docker/Dockerfile
    volumes:
      - ../..:/app
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.local
      - DATABASE_URL=postgis://postgres:postgres@db:5432/transmaint
      - REDIS_URL=redis://redis:6379/0
    command: celery -A config worker -l info
    depends_on:
      - db
      - redis

  celery-beat:
    build:
      context: ../..
      dockerfile: infrastructure/docker/Dockerfile
    volumes:
      - ../..:/app
    environment:
      - DJANGO_SETTINGS_MODULE=config.settings.local
      - DATABASE_URL=postgis://postgres:postgres@db:5432/transmaint
      - REDIS_URL=redis://redis:6379/0
    command: celery -A config beat -l info
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

### 8.4 CI/CD (GitHub Actions)

```yaml
# .github/workflows/deploy.yml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

env:
  PROJECT_ID: transmaint-prod
  REGION: us-central1
  SERVICE_NAME: transmaint-web

jobs:
  test:
    runs-on: ubuntu-latest

    services:
      postgres:
        image: postgis/postgis:17-3.4
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements/local.txt

      - name: Run linting
        run: ruff check .

      - name: Run tests
        env:
          DATABASE_URL: postgis://postgres:postgres@localhost:5432/test_db
          REDIS_URL: redis://localhost:6379/0
        run: pytest --cov=apps --cov-fail-under=80

  build-and-deploy:
    needs: test
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Google Auth
        uses: google-github-actions/auth@v2
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Set up Cloud SDK
        uses: google-github-actions/setup-gcloud@v2

      - name: Configure Docker
        run: gcloud auth configure-docker

      - name: Build and Push
        run: |
          docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:${{ github.sha }} \
            -f infrastructure/docker/Dockerfile .
          docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:${{ github.sha }}

      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy $SERVICE_NAME \
            --image gcr.io/$PROJECT_ID/$SERVICE_NAME:${{ github.sha }} \
            --region $REGION \
            --platform managed

      - name: Run migrations
        run: |
          gcloud run jobs execute transmaint-migrate --region $REGION --wait
```

---

## 9. Cronograma de Desarrollo

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         CRONOGRAMA - 20 SEMANAS                                  │
└─────────────────────────────────────────────────────────────────────────────────┘

SEMANA   1   2   3   4   5   6   7   8   9  10  11  12  13  14  15  16  17  18  19  20
         │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │   │
         ├───┴───┴───┴───┤
         │    FASE 1     │
         │    Setup      │
         │               │
         │ • Django proj │
         │ • GeoDjango   │
         │ • Auth + Roles│
         │ • Cloud Run   │
         │ • CI/CD       │
         │               │
                         ├───┴───┴───┴───┴───┴───┤
                         │        FASE 2         │
                         │     App Móvil         │
                         │                       │
                         │ • Flutter setup       │
                         │ • Offline DB          │
                         │ • Captura fotos       │
                         │ • GPS + validación    │
                         │ • Formularios         │
                         │ • Sync queue          │
                         │ • API Ninja           │
                         │                       │
                                                 ├───┴───┴───┴───┤
                                                 │    FASE 3     │
                                                 │  Portal Web   │
                                                 │               │
                                                 │ • HTMX views  │
                                                 │ • Dashboards  │
                                                 │ • Calendario  │
                                                 │ • Mapas       │
                                                 │ • Real-time   │
                                                 │               │
                                                                 ├───┴───┴───┤
                                                                 │  FASE 4   │
                                                                 │ Reportes  │
                                                                 │           │
                                                                 │ • Ambient │
                                                                 │ • Financi │
                                                                 │ • KPIs    │
                                                                 │ • Celery  │
                                                                 │           │
                                                                             ├───┴───┤
                                                                             │ FASE 5│
                                                                             │Deploy │
                                                                             │       │
                                                                             │• QA   │
                                                                             │• Pilot│
                                                                             │• Train│
                                                                             │• Live │
                                                                             │       │
```

### Detalle por Fase

| Fase | Semanas | Entregables |
|------|---------|-------------|
| **1. Setup** | 1-4 | Proyecto Django, auth, roles, Cloud Run, CI/CD |
| **2. App Móvil** | 5-10 | Flutter completo con offline, fotos, GPS, sync |
| **3. Portal Web** | 11-14 | HTMX views, dashboards, mapas, programación |
| **4. Reportes** | 15-17 | Informes ambientales, financieros, KPIs, Celery |
| **5. Deploy** | 18-20 | QA, piloto, capacitación, producción |

---

## 10. Costos Estimados (GCP)

### Infraestructura Mensual

| Servicio | Especificación | Costo/Mes USD |
|----------|----------------|---------------|
| Cloud Run (Web) | 0-10 instancias, 512MB | ~$30 |
| Cloud Run (Celery) | 1-5 instancias, 1GB | ~$50 |
| Cloud SQL | db-custom-2-4096 | ~$80 |
| Memorystore Redis | 1GB Basic | ~$35 |
| Cloud Storage | 500GB + operaciones | ~$15 |
| Cloud Load Balancing | Básico | ~$20 |
| Secrets Manager | ~20 secretos | ~$1 |
| Cloud Build | 120 min/mes | Gratis |
| **Total** | | **~$231/mes** |

### Comparativo con Propuesta Original

| Concepto | Original (GCP Full) | Actual (Cloud Run) | Ahorro |
|----------|---------------------|-------------------|--------|
| Infra/mes | $430 | $231 | 46% |
| Infra/año | $5,160 | $2,772 | $2,388 |

---

## 11. Dependencias (requirements)

```txt
# requirements/base.txt

# Django Core
Django>=5.1,<5.2
psycopg[binary]>=3.1
python-decouple>=3.8
gunicorn>=21.2

# Django Extensions
django-extensions>=3.2
django-filter>=23.5
django-widget-tweaks>=1.5

# GeoDjango
GDAL>=3.6

# APIs
djangorestframework>=3.15
django-ninja>=1.0
drf-spectacular>=0.27

# Auth & Security
djangorestframework-simplejwt>=5.3
django-axes>=6.3
django-cors-headers>=4.3
django-otp>=1.3
django-csp>=3.8

# Async Tasks
celery>=5.3
django-celery-beat>=2.5
redis>=5.0

# Cache
django-cachalot>=2.6
django-redis>=5.4

# Storage
django-storages[google]>=1.14
google-cloud-storage>=2.14

# Reports
WeasyPrint>=60.0
openpyxl>=3.1
pandas>=2.1

# Utilities
whitenoise>=6.6
sentry-sdk>=1.39
Pillow>=10.2


# requirements/local.txt
-r base.txt

# Testing
pytest>=8.0
pytest-django>=4.7
pytest-cov>=4.1
factory-boy>=3.3
faker>=22.0

# Code Quality
ruff>=0.1.14
mypy>=1.8
django-stubs>=4.2
pre-commit>=3.6

# Debug
django-debug-toolbar>=4.2
django-silk>=5.1
ipython>=8.20


# requirements/production.txt
-r base.txt

# Production server
gunicorn>=21.2
uvicorn[standard]>=0.27

# Monitoring
sentry-sdk>=1.39
```

---

## 12. Próximos Pasos

1. **Semana 1:** Crear repositorio y estructura del proyecto
2. **Semana 1:** Configurar Cloud Run y CI/CD básico
3. **Semana 2:** Implementar modelos Django y GeoDjango
4. **Semana 2:** Configurar autenticación y roles
5. **Semana 3:** Iniciar desarrollo Flutter
6. **Semana 4:** API Ninja para móvil

---

*Plan de Desarrollo v2.0 - Enero 2026*
*Stack: Django + HTMX + Flutter + Google Cloud Run*
