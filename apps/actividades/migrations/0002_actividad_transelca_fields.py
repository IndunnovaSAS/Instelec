# Generated for TransMaint - Transelca integration fields

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('lineas', '0002_tramo'),
        ('actividades', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='actividad',
            name='aviso_sap',
            field=models.CharField(
                blank=True,
                help_text='Número de aviso en el sistema SAP de Transelca',
                max_length=20,
                verbose_name='Número Aviso SAP'
            ),
        ),
        migrations.AddField(
            model_name='actividad',
            name='porcentaje_avance',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Porcentaje de avance de la actividad (0-100)',
                max_digits=5,
                verbose_name='Porcentaje de avance'
            ),
        ),
        migrations.AddField(
            model_name='actividad',
            name='valor_facturacion',
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text='Valor total de facturación de la actividad',
                max_digits=14,
                verbose_name='Valor facturación'
            ),
        ),
        migrations.AddField(
            model_name='actividad',
            name='tramo',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='actividades',
                to='lineas.tramo',
                verbose_name='Tramo'
            ),
        ),
        migrations.AddField(
            model_name='tipoactividad',
            name='rendimiento_estandar_vanos',
            field=models.PositiveIntegerField(
                default=3,
                help_text='Rendimiento estándar en vanos por día para este tipo de actividad',
                verbose_name='Vanos por día esperados'
            ),
        ),
        migrations.AddIndex(
            model_name='actividad',
            index=models.Index(fields=['aviso_sap'], name='actividades_aviso_s_6a007f_idx'),
        ),
        migrations.AddIndex(
            model_name='actividad',
            index=models.Index(fields=['tramo'], name='actividades_tramo_i_a736b9_idx'),
        ),
    ]
