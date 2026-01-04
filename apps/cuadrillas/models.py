"""
Models for work crews (cuadrillas) management.
"""
from django.db import models
from apps.core.models import BaseModel


class Vehiculo(BaseModel):
    """
    Vehicle model for crew transportation.
    """

    class TipoVehiculo(models.TextChoices):
        CAMIONETA = 'CAMIONETA', 'Camioneta'
        CAMION = 'CAMION', 'Camión'
        GRUA = 'GRUA', 'Grúa'
        OTRO = 'OTRO', 'Otro'

    placa = models.CharField(
        'Placa',
        max_length=10,
        unique=True
    )
    tipo = models.CharField(
        'Tipo',
        max_length=20,
        choices=TipoVehiculo.choices,
        default=TipoVehiculo.CAMIONETA
    )
    marca = models.CharField(
        'Marca',
        max_length=50,
        blank=True
    )
    modelo = models.CharField(
        'Modelo',
        max_length=50,
        blank=True
    )
    ano = models.PositiveIntegerField(
        'Año',
        null=True,
        blank=True
    )
    capacidad_personas = models.PositiveIntegerField(
        'Capacidad (personas)',
        default=5
    )
    costo_dia = models.DecimalField(
        'Costo por día',
        max_digits=12,
        decimal_places=2,
        default=0
    )
    activo = models.BooleanField(
        'Activo',
        default=True
    )
    observaciones = models.TextField(
        'Observaciones',
        blank=True
    )

    class Meta:
        db_table = 'vehiculos'
        verbose_name = 'Vehículo'
        verbose_name_plural = 'Vehículos'
        ordering = ['placa']

    def __str__(self):
        return f"{self.placa} - {self.marca} {self.modelo}"


class Cuadrilla(BaseModel):
    """
    Work crew model.
    """

    codigo = models.CharField(
        'Código',
        max_length=20,
        unique=True,
        help_text='Código único de la cuadrilla (ej: CUA-001)'
    )
    nombre = models.CharField(
        'Nombre',
        max_length=100
    )
    supervisor = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cuadrillas_supervisadas',
        verbose_name='Supervisor',
        limit_choices_to={'rol': 'supervisor'}
    )
    vehiculo = models.ForeignKey(
        Vehiculo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cuadrillas',
        verbose_name='Vehículo asignado'
    )
    linea_asignada = models.ForeignKey(
        'lineas.Linea',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cuadrillas',
        verbose_name='Línea asignada'
    )
    activa = models.BooleanField(
        'Activa',
        default=True
    )
    observaciones = models.TextField(
        'Observaciones',
        blank=True
    )

    class Meta:
        db_table = 'cuadrillas'
        verbose_name = 'Cuadrilla'
        verbose_name_plural = 'Cuadrillas'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    @property
    def miembros_activos(self):
        return self.miembros.filter(activo=True)

    @property
    def total_miembros(self):
        return self.miembros_activos.count()


class CuadrillaMiembro(BaseModel):
    """
    Crew member assignment.
    """

    class RolCuadrilla(models.TextChoices):
        SUPERVISOR = 'SUPERVISOR', 'Supervisor'
        LINIERO = 'LINIERO', 'Liniero'
        AYUDANTE = 'AYUDANTE', 'Ayudante'

    cuadrilla = models.ForeignKey(
        Cuadrilla,
        on_delete=models.CASCADE,
        related_name='miembros',
        verbose_name='Cuadrilla'
    )
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='asignaciones_cuadrilla',
        verbose_name='Usuario'
    )
    rol_cuadrilla = models.CharField(
        'Rol en cuadrilla',
        max_length=20,
        choices=RolCuadrilla.choices,
        default=RolCuadrilla.LINIERO
    )
    fecha_inicio = models.DateField(
        'Fecha de inicio'
    )
    fecha_fin = models.DateField(
        'Fecha de fin',
        null=True,
        blank=True
    )
    activo = models.BooleanField(
        'Activo',
        default=True
    )

    class Meta:
        db_table = 'cuadrilla_miembros'
        verbose_name = 'Miembro de Cuadrilla'
        verbose_name_plural = 'Miembros de Cuadrilla'
        unique_together = ['cuadrilla', 'usuario', 'activo']
        ordering = ['cuadrilla', 'rol_cuadrilla', 'usuario__first_name']

    def __str__(self):
        return f"{self.usuario.get_full_name()} - {self.cuadrilla.codigo}"


class TrackingUbicacion(BaseModel):
    """
    Real-time location tracking for crews.
    """

    cuadrilla = models.ForeignKey(
        Cuadrilla,
        on_delete=models.CASCADE,
        related_name='ubicaciones',
        verbose_name='Cuadrilla'
    )
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='ubicaciones_tracking',
        verbose_name='Usuario'
    )
    latitud = models.DecimalField(
        'Latitud',
        max_digits=10,
        decimal_places=8
    )
    longitud = models.DecimalField(
        'Longitud',
        max_digits=11,
        decimal_places=8
    )
    precision_metros = models.DecimalField(
        'Precisión (metros)',
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    velocidad = models.DecimalField(
        'Velocidad (km/h)',
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    bateria = models.PositiveIntegerField(
        'Nivel batería (%)',
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'tracking_ubicacion'
        verbose_name = 'Tracking de Ubicación'
        verbose_name_plural = 'Tracking de Ubicaciones'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['cuadrilla', '-created_at']),
            models.Index(fields=['usuario', '-created_at']),
        ]

    def __str__(self):
        return f"{self.cuadrilla.codigo} - {self.created_at}"
