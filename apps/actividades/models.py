"""
Models for activity scheduling and management.
"""
from django.db import models
from apps.core.models import BaseModel
from apps.core.validators import (
    campos_formulario_validator,
    datos_importados_validator,
)


class TipoActividad(BaseModel):
    """
    Activity type configuration with dynamic form fields.
    """

    class Categoria(models.TextChoices):
        PODA = 'PODA', 'Poda de Vegetación'
        HERRAJES = 'HERRAJES', 'Cambio de Herrajes'
        AISLADORES = 'AISLADORES', 'Cambio de Aisladores'
        INSPECCION = 'INSPECCION', 'Inspección'
        LIMPIEZA = 'LIMPIEZA', 'Limpieza'
        SEÑALIZACION = 'SEÑALIZACION', 'Señalización'
        MEDICION = 'MEDICION', 'Medición'
        OTRO = 'OTRO', 'Otro'

    codigo = models.CharField(
        'Código',
        max_length=20,
        unique=True
    )
    nombre = models.CharField(
        'Nombre',
        max_length=100
    )
    categoria = models.CharField(
        'Categoría',
        max_length=20,
        choices=Categoria.choices
    )
    descripcion = models.TextField(
        'Descripción',
        blank=True
    )
    requiere_fotos_antes = models.BooleanField(
        'Requiere fotos ANTES',
        default=True
    )
    requiere_fotos_durante = models.BooleanField(
        'Requiere fotos DURANTE',
        default=True
    )
    requiere_fotos_despues = models.BooleanField(
        'Requiere fotos DESPUÉS',
        default=True
    )
    min_fotos = models.PositiveIntegerField(
        'Mínimo de fotos',
        default=3
    )
    campos_formulario = models.JSONField(
        'Campos del formulario',
        default=dict,
        blank=True,
        validators=[campos_formulario_validator],
        help_text='Configuración de campos dinámicos en formato JSON'
    )
    tiempo_estimado_horas = models.DecimalField(
        'Tiempo estimado (horas)',
        max_digits=4,
        decimal_places=2,
        default=2
    )
    rendimiento_estandar_vanos = models.PositiveIntegerField(
        'Vanos por día esperados',
        default=3,
        help_text='Rendimiento estándar en vanos por día para este tipo de actividad'
    )
    activo = models.BooleanField(
        'Activo',
        default=True
    )

    class Meta:
        db_table = 'tipos_actividad'
        verbose_name = 'Tipo de Actividad'
        verbose_name_plural = 'Tipos de Actividad'
        ordering = ['categoria', 'nombre']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class ProgramacionMensual(BaseModel):
    """
    Monthly programming imported from client's Excel.
    """

    anio = models.PositiveIntegerField('Año')
    mes = models.PositiveIntegerField('Mes')
    linea = models.ForeignKey(
        'lineas.Linea',
        on_delete=models.CASCADE,
        related_name='programaciones',
        verbose_name='Línea'
    )
    archivo_origen = models.FileField(
        'Archivo Excel origen',
        upload_to='programacion/excel/',
        blank=True,
        null=True
    )
    datos_importados = models.JSONField(
        'Datos importados',
        default=dict,
        blank=True,
        validators=[datos_importados_validator]
    )
    total_actividades = models.PositiveIntegerField(
        'Total actividades',
        default=0
    )
    aprobado = models.BooleanField(
        'Aprobado',
        default=False
    )
    aprobado_por = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='programaciones_aprobadas',
        verbose_name='Aprobado por'
    )
    fecha_aprobacion = models.DateTimeField(
        'Fecha de aprobación',
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'programacion_mensual'
        verbose_name = 'Programación Mensual'
        verbose_name_plural = 'Programaciones Mensuales'
        unique_together = ['anio', 'mes', 'linea']
        ordering = ['-anio', '-mes', 'linea']

    def __str__(self):
        return f"Programación {self.linea.codigo} - {self.mes}/{self.anio}"


class Actividad(BaseModel):
    """
    Scheduled maintenance activity.
    """

    class Estado(models.TextChoices):
        PENDIENTE = 'PENDIENTE', 'Pendiente'
        PROGRAMADA = 'PROGRAMADA', 'Programada'
        EN_CURSO = 'EN_CURSO', 'En Curso'
        COMPLETADA = 'COMPLETADA', 'Completada'
        CANCELADA = 'CANCELADA', 'Cancelada'
        REPROGRAMADA = 'REPROGRAMADA', 'Reprogramada'

    class Prioridad(models.TextChoices):
        BAJA = 'BAJA', 'Baja'
        NORMAL = 'NORMAL', 'Normal'
        ALTA = 'ALTA', 'Alta'
        URGENTE = 'URGENTE', 'Urgente'

    # Relationships
    linea = models.ForeignKey(
        'lineas.Linea',
        on_delete=models.CASCADE,
        related_name='actividades',
        verbose_name='Línea'
    )
    torre = models.ForeignKey(
        'lineas.Torre',
        on_delete=models.CASCADE,
        related_name='actividades',
        verbose_name='Torre'
    )
    tipo_actividad = models.ForeignKey(
        TipoActividad,
        on_delete=models.PROTECT,
        related_name='actividades',
        verbose_name='Tipo de actividad'
    )
    cuadrilla = models.ForeignKey(
        'cuadrillas.Cuadrilla',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actividades',
        verbose_name='Cuadrilla asignada'
    )
    programacion = models.ForeignKey(
        ProgramacionMensual,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actividades',
        verbose_name='Programación mensual'
    )
    tramo = models.ForeignKey(
        'lineas.Tramo',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='actividades',
        verbose_name='Tramo'
    )

    # SAP Integration
    aviso_sap = models.CharField(
        'Número Aviso SAP',
        max_length=20,
        blank=True,
        help_text='Número de aviso en el sistema SAP de Transelca'
    )

    # Progress and billing
    porcentaje_avance = models.DecimalField(
        'Porcentaje de avance',
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text='Porcentaje de avance de la actividad (0-100)'
    )
    valor_facturacion = models.DecimalField(
        'Valor facturación',
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text='Valor total de facturación de la actividad'
    )

    # Scheduling
    fecha_programada = models.DateField('Fecha programada')
    fecha_reprogramada = models.DateField(
        'Fecha reprogramada',
        null=True,
        blank=True
    )
    hora_inicio_estimada = models.TimeField(
        'Hora inicio estimada',
        null=True,
        blank=True
    )

    # Status
    estado = models.CharField(
        'Estado',
        max_length=20,
        choices=Estado.choices,
        default=Estado.PENDIENTE
    )
    prioridad = models.CharField(
        'Prioridad',
        max_length=10,
        choices=Prioridad.choices,
        default=Prioridad.NORMAL
    )

    # Notes
    observaciones_programacion = models.TextField(
        'Observaciones de programación',
        blank=True
    )
    motivo_reprogramacion = models.TextField(
        'Motivo de reprogramación',
        blank=True
    )
    motivo_cancelacion = models.TextField(
        'Motivo de cancelación',
        blank=True
    )

    class Meta:
        db_table = 'actividades'
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'
        ordering = ['-fecha_programada', 'prioridad', 'linea', 'torre']
        indexes = [
            models.Index(fields=['fecha_programada', 'estado']),
            models.Index(fields=['cuadrilla', 'fecha_programada']),
            models.Index(fields=['linea', 'fecha_programada']),
            models.Index(fields=['aviso_sap']),
            models.Index(fields=['tramo']),
        ]

    def __str__(self):
        return f"{self.tipo_actividad.nombre} - Torre {self.torre.numero} ({self.fecha_programada})"

    @property
    def fecha_efectiva(self):
        """Returns the effective date (reprogrammed or original)."""
        return self.fecha_reprogramada or self.fecha_programada

    @property
    def esta_atrasada(self):
        """Check if activity is overdue."""
        from django.utils import timezone
        if self.estado in [self.Estado.COMPLETADA, self.Estado.CANCELADA]:
            return False
        return self.fecha_efectiva < timezone.now().date()

    @property
    def produccion_proporcional(self):
        """Calcula la producción proporcional al avance: porcentaje_avance × valor_facturacion."""
        return (self.porcentaje_avance / 100) * self.valor_facturacion

    @property
    def rendimiento_esperado_diario(self):
        """Retorna el rendimiento esperado en vanos por día según el tipo de actividad."""
        return self.tipo_actividad.rendimiento_estandar_vanos

    def actualizar_avance(self, nuevo_porcentaje):
        """Actualiza el porcentaje de avance de la actividad."""
        from decimal import Decimal
        self.porcentaje_avance = Decimal(str(nuevo_porcentaje))
        if self.porcentaje_avance >= 100:
            self.estado = self.Estado.COMPLETADA
        self.save(update_fields=['porcentaje_avance', 'estado', 'updated_at'])

    def iniciar(self, usuario):
        """Mark activity as started."""
        self.estado = self.Estado.EN_CURSO
        self.save(update_fields=['estado', 'updated_at'])

    def completar(self):
        """Mark activity as completed."""
        self.estado = self.Estado.COMPLETADA
        self.save(update_fields=['estado', 'updated_at'])

    def cancelar(self, motivo: str):
        """Cancel activity with reason."""
        self.estado = self.Estado.CANCELADA
        self.motivo_cancelacion = motivo
        self.save(update_fields=['estado', 'motivo_cancelacion', 'updated_at'])

    def reprogramar(self, nueva_fecha, motivo: str):
        """Reschedule activity."""
        self.estado = self.Estado.REPROGRAMADA
        self.fecha_reprogramada = nueva_fecha
        self.motivo_reprogramacion = motivo
        self.save(update_fields=['estado', 'fecha_reprogramada', 'motivo_reprogramacion', 'updated_at'])
