"""
Models for transmission lines, towers, and easements.
"""
from django.contrib.gis.db import models as gis_models
from django.db import models
from apps.core.models import BaseModel


class Linea(BaseModel):
    """
    Transmission line model.
    """

    class Cliente(models.TextChoices):
        TRANSELCA = 'TRANSELCA', 'Transelca'
        INTERCOLOMBIA = 'INTERCOLOMBIA', 'Intercolombia'

    codigo = models.CharField(
        'Código',
        max_length=20,
        unique=True,
        help_text='Código único de la línea (ej: L-838)'
    )
    nombre = models.CharField(
        'Nombre',
        max_length=150,
        help_text='Nombre descriptivo de la línea'
    )
    cliente = models.CharField(
        'Cliente',
        max_length=20,
        choices=Cliente.choices,
        default=Cliente.TRANSELCA
    )
    longitud_km = models.DecimalField(
        'Longitud (km)',
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    tension_kv = models.PositiveIntegerField(
        'Tensión (kV)',
        null=True,
        blank=True,
        help_text='Tensión nominal en kilovoltios'
    )
    municipios = models.CharField(
        'Municipios',
        max_length=500,
        blank=True,
        help_text='Municipios por donde pasa la línea'
    )
    departamento = models.CharField(
        'Departamento',
        max_length=100,
        blank=True
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
        db_table = 'lineas'
        verbose_name = 'Línea'
        verbose_name_plural = 'Líneas'
        ordering = ['codigo']

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"

    @property
    def total_torres(self):
        return self.torres.count()


class Torre(BaseModel):
    """
    Tower/structure model with geographic location.
    """

    class TipoTorre(models.TextChoices):
        SUSPENSION = 'SUSPENSION', 'Suspensión'
        ANCLAJE = 'ANCLAJE', 'Anclaje'
        TERMINAL = 'TERMINAL', 'Terminal'
        REMATE = 'REMATE', 'Remate'
        DERIVACION = 'DERIVACION', 'Derivación'

    class EstadoTorre(models.TextChoices):
        BUENO = 'BUENO', 'Bueno'
        REGULAR = 'REGULAR', 'Regular'
        MALO = 'MALO', 'Malo'
        CRITICO = 'CRITICO', 'Crítico'

    linea = models.ForeignKey(
        Linea,
        on_delete=models.CASCADE,
        related_name='torres',
        verbose_name='Línea'
    )
    numero = models.CharField(
        'Número',
        max_length=20,
        help_text='Número o código de la torre'
    )
    tipo = models.CharField(
        'Tipo',
        max_length=20,
        choices=TipoTorre.choices,
        default=TipoTorre.SUSPENSION
    )
    estado = models.CharField(
        'Estado',
        max_length=20,
        choices=EstadoTorre.choices,
        default=EstadoTorre.BUENO
    )
    latitud = models.DecimalField(
        'Latitud',
        max_digits=10,
        decimal_places=8,
        help_text='Latitud en grados decimales'
    )
    longitud = models.DecimalField(
        'Longitud',
        max_digits=11,
        decimal_places=8,
        help_text='Longitud en grados decimales'
    )
    altitud = models.DecimalField(
        'Altitud (msnm)',
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )
    geometria = gis_models.PointField(
        'Ubicación geográfica',
        srid=4326,
        null=True,
        blank=True
    )
    altura_estructura = models.DecimalField(
        'Altura estructura (m)',
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    propietario_predio = models.CharField(
        'Propietario del predio',
        max_length=200,
        blank=True
    )
    vereda = models.CharField(
        'Vereda',
        max_length=100,
        blank=True
    )
    municipio = models.CharField(
        'Municipio',
        max_length=100,
        blank=True
    )
    observaciones = models.TextField(
        'Observaciones',
        blank=True
    )

    class Meta:
        db_table = 'torres'
        verbose_name = 'Torre'
        verbose_name_plural = 'Torres'
        unique_together = ['linea', 'numero']
        ordering = ['linea', 'numero']

    def __str__(self):
        return f"Torre {self.numero} - {self.linea.codigo}"

    def save(self, *args, **kwargs):
        # Auto-generate geometry from lat/lon
        if self.latitud and self.longitud:
            from django.contrib.gis.geos import Point
            self.geometria = Point(
                float(self.longitud),
                float(self.latitud),
                srid=4326
            )
        super().save(*args, **kwargs)


class PoligonoServidumbre(BaseModel):
    """
    Easement polygon for towers.
    Defines the authorized work area around a tower.
    """

    linea = models.ForeignKey(
        Linea,
        on_delete=models.CASCADE,
        related_name='poligonos',
        verbose_name='Línea',
        null=True,
        blank=True
    )
    torre = models.ForeignKey(
        Torre,
        on_delete=models.CASCADE,
        related_name='poligonos',
        verbose_name='Torre',
        null=True,
        blank=True
    )
    nombre = models.CharField(
        'Nombre',
        max_length=100,
        blank=True
    )
    geometria = gis_models.PolygonField(
        'Geometría',
        srid=4326
    )
    area_hectareas = models.DecimalField(
        'Área (hectáreas)',
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True
    )
    ancho_franja = models.DecimalField(
        'Ancho de franja (m)',
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True
    )
    observaciones = models.TextField(
        'Observaciones',
        blank=True
    )

    class Meta:
        db_table = 'poligonos_servidumbre'
        verbose_name = 'Polígono de Servidumbre'
        verbose_name_plural = 'Polígonos de Servidumbre'

    def __str__(self):
        if self.torre:
            return f"Servidumbre - Torre {self.torre.numero}"
        return f"Servidumbre - {self.nombre or self.id}"

    def punto_dentro(self, latitud: float, longitud: float) -> bool:
        """
        Check if a point is within the easement polygon.

        Args:
            latitud: Latitude in decimal degrees
            longitud: Longitude in decimal degrees

        Returns:
            True if point is inside the polygon
        """
        from django.contrib.gis.geos import Point
        punto = Point(longitud, latitud, srid=4326)
        return self.geometria.contains(punto)

    def save(self, *args, **kwargs):
        # Calculate area if geometry is provided
        if self.geometria:
            # Transform to a projected CRS for accurate area calculation
            geom_projected = self.geometria.transform(3857, clone=True)
            self.area_hectareas = geom_projected.area / 10000  # m² to hectares
        super().save(*args, **kwargs)
