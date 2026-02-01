# Generated for TransMaint - ambiental models

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('lineas', '0001_initial'),
        ('usuarios', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='InformeAmbiental',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creacion')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Fecha de actualizacion')),
                ('periodo_mes', models.PositiveIntegerField(verbose_name='Mes')),
                ('periodo_anio', models.PositiveIntegerField(verbose_name='Ano')),
                ('estado', models.CharField(
                    choices=[
                        ('BORRADOR', 'Borrador'),
                        ('EN_REVISION', 'En Revision'),
                        ('APROBADO', 'Aprobado'),
                        ('ENVIADO', 'Enviado al Cliente'),
                        ('RECHAZADO', 'Rechazado')
                    ],
                    default='BORRADOR',
                    max_length=20,
                    verbose_name='Estado'
                )),
                ('total_actividades', models.PositiveIntegerField(default=0, verbose_name='Total actividades')),
                ('total_podas', models.PositiveIntegerField(default=0, verbose_name='Total podas')),
                ('hectareas_intervenidas', models.DecimalField(
                    decimal_places=2,
                    default=0,
                    max_digits=10,
                    verbose_name='Hectareas intervenidas'
                )),
                ('m3_vegetacion', models.DecimalField(
                    decimal_places=2,
                    default=0,
                    max_digits=10,
                    verbose_name='M3 vegetacion removida'
                )),
                ('fecha_elaboracion', models.DateTimeField(
                    blank=True,
                    null=True,
                    verbose_name='Fecha elaboracion'
                )),
                ('fecha_revision', models.DateTimeField(
                    blank=True,
                    null=True,
                    verbose_name='Fecha revision'
                )),
                ('fecha_aprobacion', models.DateTimeField(
                    blank=True,
                    null=True,
                    verbose_name='Fecha aprobacion'
                )),
                ('fecha_envio', models.DateTimeField(
                    blank=True,
                    null=True,
                    verbose_name='Fecha envio'
                )),
                ('url_pdf', models.URLField(blank=True, verbose_name='URL PDF')),
                ('url_excel', models.URLField(blank=True, verbose_name='URL Excel')),
                ('observaciones', models.TextField(blank=True, verbose_name='Observaciones')),
                ('linea', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='informes_ambientales',
                    to='lineas.linea',
                    verbose_name='Linea'
                )),
                ('elaborado_por', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='informes_elaborados',
                    to='usuarios.usuario',
                    verbose_name='Elaborado por'
                )),
                ('revisado_por', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='informes_revisados',
                    to='usuarios.usuario',
                    verbose_name='Revisado por'
                )),
                ('aprobado_por', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='informes_ambientales_aprobados',
                    to='usuarios.usuario',
                    verbose_name='Aprobado por'
                )),
            ],
            options={
                'verbose_name': 'Informe Ambiental',
                'verbose_name_plural': 'Informes Ambientales',
                'db_table': 'informes_ambientales',
                'ordering': ['-periodo_anio', '-periodo_mes', 'linea'],
                'unique_together': {('periodo_mes', 'periodo_anio', 'linea')},
            },
        ),
        migrations.CreateModel(
            name='PermisoServidumbre',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de creacion')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Fecha de actualizacion')),
                ('propietario_nombre', models.CharField(max_length=200, verbose_name='Nombre del propietario')),
                ('propietario_documento', models.CharField(blank=True, max_length=20, verbose_name='Documento de identidad')),
                ('propietario_telefono', models.CharField(blank=True, max_length=20, verbose_name='Telefono')),
                ('predio_nombre', models.CharField(blank=True, max_length=200, verbose_name='Nombre del predio')),
                ('predio_matricula', models.CharField(blank=True, max_length=50, verbose_name='Matricula inmobiliaria')),
                ('fecha_autorizacion', models.DateField(verbose_name='Fecha de autorizacion')),
                ('fecha_vencimiento', models.DateField(blank=True, null=True, verbose_name='Fecha de vencimiento')),
                ('actividades_autorizadas', models.TextField(blank=True, verbose_name='Actividades autorizadas')),
                ('url_documento_firmado', models.URLField(blank=True, verbose_name='URL documento firmado')),
                ('url_firma_digital', models.URLField(blank=True, verbose_name='URL firma digital')),
                ('observaciones', models.TextField(blank=True, verbose_name='Observaciones')),
                ('torre', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='permisos_servidumbre',
                    to='lineas.torre',
                    verbose_name='Torre'
                )),
            ],
            options={
                'verbose_name': 'Permiso de Servidumbre',
                'verbose_name_plural': 'Permisos de Servidumbre',
                'db_table': 'permisos_servidumbre',
                'ordering': ['-fecha_autorizacion'],
            },
        ),
    ]
