# Generated for TransMaint - Avance and Pendientes fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('campo', '0002_add_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrocampo',
            name='porcentaje_avance_reportado',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Porcentaje de avance reportado en este registro (0-100)',
                max_digits=5,
                verbose_name='Porcentaje de avance reportado'
            ),
        ),
        migrations.AddField(
            model_name='registrocampo',
            name='tiene_pendiente',
            field=models.BooleanField(
                default=False,
                help_text='Indica si hay algún pendiente o condición especial',
                verbose_name='Tiene pendiente'
            ),
        ),
        migrations.AddField(
            model_name='registrocampo',
            name='tipo_pendiente',
            field=models.CharField(
                blank=True,
                choices=[
                    ('ACCESO', 'Problema de acceso'),
                    ('PERMISOS', 'Falta de permisos'),
                    ('CLIMA', 'Condiciones climáticas'),
                    ('MATERIAL', 'Falta de material'),
                    ('EQUIPO', 'Falta de equipo'),
                    ('SEGURIDAD', 'Condición de seguridad'),
                    ('PROPIETARIO', 'Problema con propietario'),
                    ('OTRO', 'Otro'),
                ],
                help_text='Clasificación del tipo de pendiente',
                max_length=20,
                verbose_name='Tipo de pendiente'
            ),
        ),
        migrations.AddField(
            model_name='registrocampo',
            name='descripcion_pendiente',
            field=models.TextField(
                blank=True,
                help_text='Descripción detallada del pendiente o condición especial',
                verbose_name='Descripción del pendiente'
            ),
        ),
        migrations.AddIndex(
            model_name='registrocampo',
            index=models.Index(fields=['tiene_pendiente'], name='idx_registro_pendiente'),
        ),
    ]
