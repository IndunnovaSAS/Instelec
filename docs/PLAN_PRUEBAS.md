# Plan de Pruebas - TransMaint

## Índice
1. [Resumen Ejecutivo](#resumen-ejecutivo)
2. [Alcance de Pruebas](#alcance-de-pruebas)
3. [Estrategia de Pruebas](#estrategia-de-pruebas)
4. [Tests por Módulo](#tests-por-módulo)
5. [Tests de Integración](#tests-de-integración)
6. [Tests E2E](#tests-e2e)
7. [Criterios de Aceptación](#criterios-de-aceptación)

---

## Resumen Ejecutivo

Este documento define el plan de pruebas exhaustivo para el sistema TransMaint, cubriendo:
- **11 módulos Django** con tests unitarios
- **Integración entre módulos** críticos
- **Flujos E2E** de operaciones principales
- **Cobertura objetivo**: 80%+

---

## Alcance de Pruebas

### Módulos a Probar

| Módulo | Prioridad | Complejidad | Tests Estimados |
|--------|-----------|-------------|-----------------|
| usuarios | Alta | Media | 25 |
| lineas | Alta | Alta | 30 |
| actividades | Crítica | Alta | 45 |
| campo | Crítica | Alta | 40 |
| indicadores | Alta | Media | 35 |
| cuadrillas | Media | Media | 20 |
| ambiental | Media | Media | 25 |
| financiero | Alta | Alta | 35 |
| notificaciones | Baja | Baja | 15 |
| core | Media | Baja | 10 |
| **API Mobile** | Crítica | Alta | 50 |

**Total estimado: ~330 tests**

---

## Estrategia de Pruebas

### Niveles de Pruebas

```
┌─────────────────────────────────────────┐
│           Tests E2E (10%)               │  ← Flujos completos
├─────────────────────────────────────────┤
│      Tests de Integración (30%)         │  ← Entre módulos
├─────────────────────────────────────────┤
│        Tests Unitarios (60%)            │  ← Por componente
└─────────────────────────────────────────┘
```

### Herramientas

- **pytest**: Framework principal
- **pytest-django**: Integración Django
- **pytest-cov**: Cobertura de código
- **factory_boy**: Generación de datos
- **freezegun**: Control de tiempo
- **responses**: Mock de APIs externas

---

## Tests por Módulo

### 1. Módulo: `usuarios`

#### 1.1 Modelos
```python
# tests/unit/usuarios/test_models.py

class TestUsuarioModel:
    - test_create_usuario_basico
    - test_create_superuser
    - test_email_as_username
    - test_rol_choices
    - test_cargo_field
    - test_cuadrilla_actual_property
    - test_is_liniero_property
    - test_is_supervisor_property
    - test_full_name_property
    - test_str_representation

class TestUsuarioManager:
    - test_create_user_without_email_raises_error
    - test_create_user_normalizes_email
    - test_create_superuser_sets_flags
```

#### 1.2 Vistas
```python
# tests/unit/usuarios/test_views.py

class TestLoginView:
    - test_login_page_renders
    - test_login_with_valid_credentials
    - test_login_with_invalid_credentials
    - test_login_redirects_authenticated_user
    - test_login_remembers_next_url

class TestProfileView:
    - test_profile_requires_authentication
    - test_profile_shows_user_data
    - test_profile_update_success
```

#### 1.3 API
```python
# tests/unit/usuarios/test_api.py

class TestAuthAPI:
    - test_login_returns_tokens
    - test_login_invalid_credentials_401
    - test_refresh_token
    - test_me_endpoint_authenticated
    - test_me_endpoint_unauthenticated_401
    - test_logout_invalidates_token
```

---

### 2. Módulo: `lineas`

#### 2.1 Modelos
```python
# tests/unit/lineas/test_models.py

class TestLineaModel:
    - test_create_linea
    - test_linea_codigo_unique
    - test_linea_str_representation
    - test_linea_activa_default_true
    - test_linea_cliente_field
    - test_total_torres_property

class TestTorreModel:
    - test_create_torre
    - test_torre_with_coordinates
    - test_torre_numero_unique_per_linea
    - test_torre_tipo_choices
    - test_torre_estado_choices
    - test_torre_ubicacion_point_field

class TestPoligonoServidumbreModel:
    - test_create_poligono
    - test_poligono_geometria_field
    - test_punto_dentro_true
    - test_punto_dentro_false
    - test_calcular_area
```

#### 2.2 Vistas
```python
# tests/unit/lineas/test_views.py

class TestLineaListView:
    - test_list_requires_auth
    - test_list_shows_active_lineas
    - test_filter_by_cliente
    - test_search_by_nombre
    - test_pagination_works

class TestMapaLineasView:
    - test_mapa_renders
    - test_mapa_includes_geojson_data
    - test_mapa_shows_all_torres
```

---

### 3. Módulo: `actividades`

#### 3.1 Modelos
```python
# tests/unit/actividades/test_models.py

class TestActividadModel:
    - test_create_actividad
    - test_actividad_estado_transitions
    - test_actividad_prioridad_ordering
    - test_actividad_fecha_programada_required
    - test_actividad_str_representation
    - test_puede_iniciar_pendiente_true
    - test_puede_iniciar_completada_false
    - test_puede_completar_en_curso_true

class TestTipoActividadModel:
    - test_create_tipo_actividad
    - test_campos_formulario_json
    - test_requiere_fotos_flags
    - test_tiempo_estimado_horas

class TestProgramacionMensualModel:
    - test_create_programacion
    - test_aprobar_programacion
    - test_rechazar_programacion
```

#### 3.2 Vistas
```python
# tests/unit/actividades/test_views.py

class TestActividadListView:
    - test_list_all_actividades
    - test_filter_by_estado
    - test_filter_by_linea
    - test_filter_by_cuadrilla
    - test_filter_by_fecha_range
    - test_htmx_partial_response

class TestCalendarioView:
    - test_calendario_current_month
    - test_calendario_navigation
    - test_actividades_grouped_by_day
```

#### 3.3 API
```python
# tests/unit/actividades/test_api.py

class TestActividadesAPI:
    - test_listar_tipos_actividad
    - test_mis_actividades_empty_without_cuadrilla
    - test_mis_actividades_returns_assigned
    - test_mis_actividades_filter_by_fecha
    - test_obtener_actividad_detail
    - test_iniciar_actividad_creates_registro
    - test_iniciar_actividad_checks_location
    - test_iniciar_actividad_updates_estado
```

---

### 4. Módulo: `campo`

#### 4.1 Modelos
```python
# tests/unit/campo/test_models.py

class TestRegistroCampoModel:
    - test_create_registro
    - test_registro_fecha_inicio_required
    - test_registro_sincronizado_default_false
    - test_registro_datos_formulario_json
    - test_registro_duracion_property
    - test_evidencias_completas_property

class TestEvidenciaModel:
    - test_create_evidencia
    - test_evidencia_tipo_choices
    - test_evidencia_coordenadas
    - test_evidencia_validacion_ia_json
    - test_evidencia_url_thumbnail
```

#### 4.2 Validadores
```python
# tests/unit/campo/test_validators.py

class TestPhotoValidator:
    - test_valid_image_passes
    - test_invalid_format_fails
    - test_low_resolution_fails
    - test_dark_image_fails
    - test_overexposed_image_fails
    - test_blurry_image_fails

class TestGPSValidation:
    - test_gps_within_range_passes
    - test_gps_out_of_range_fails
    - test_missing_gps_warning

class TestTimestampValidation:
    - test_timestamp_within_range_passes
    - test_timestamp_old_fails
    - test_missing_timestamp_warning

class TestPhotoSetValidation:
    - test_complete_set_passes
    - test_missing_antes_fails
    - test_missing_despues_fails
```

#### 4.3 Tasks
```python
# tests/unit/campo/test_tasks.py

class TestProcesarEvidenciaTask:
    - test_generates_thumbnail
    - test_validates_image_quality
    - test_stamps_metadata
    - test_retries_on_failure
```

---

### 5. Módulo: `indicadores`

#### 5.1 Calculadoras
```python
# tests/unit/indicadores/test_calculators.py

class TestGestionMantenimiento:
    - test_no_activities_returns_zero
    - test_all_completed_returns_100
    - test_partial_completion_calculates_percentage
    - test_cancelled_activities_excluded

class TestEjecucionMantenimiento:
    - test_on_time_completion_100
    - test_late_completion_reduces_score
    - test_no_completed_returns_zero

class TestGestionAmbiental:
    - test_report_on_time_100
    - test_report_late_0
    - test_report_missing_0

class TestCalidadInformacion:
    - test_complete_records_100
    - test_incomplete_records_reduce_score
    - test_no_records_returns_zero

class TestSeguridadIndustrial:
    - test_no_accidents_100
    - test_accidents_reduce_score
    - test_working_days_calculation

class TestCumplimientoCronograma:
    - test_started_on_time_100
    - test_late_start_reduces_score

class TestIndiceGlobal:
    - test_weighted_average_calculation
    - test_all_weights_sum_to_one
    - test_returns_details_per_category
```

#### 5.2 Tasks
```python
# tests/unit/indicadores/test_tasks.py

class TestCalcularIndicadoresMensuales:
    - test_calculates_for_all_lines
    - test_saves_to_database
    - test_uses_previous_month_by_default

class TestVerificarAlertas:
    - test_detects_below_threshold
    - test_groups_by_line
    - test_notifies_supervisors
```

---

### 6. Módulo: `cuadrillas`

#### 6.1 Modelos
```python
# tests/unit/cuadrillas/test_models.py

class TestCuadrillaModel:
    - test_create_cuadrilla
    - test_cuadrilla_codigo_unique
    - test_cuadrilla_activa_default
    - test_miembros_count_property

class TestCuadrillaMiembroModel:
    - test_add_member_to_cuadrilla
    - test_member_roles
    - test_fecha_inicio_required

class TestUbicacionCuadrillaModel:
    - test_track_location
    - test_location_timestamp
    - test_latest_location_property
```

---

### 7. Módulo: `ambiental`

#### 7.1 Modelos
```python
# tests/unit/ambiental/test_models.py

class TestInformeAmbientalModel:
    - test_create_informe
    - test_informe_estado_transitions
    - test_informe_unique_per_period

class TestPermisoServidumbreModel:
    - test_create_permiso
    - test_permiso_vigente
    - test_permiso_vencido
    - test_permiso_por_vencer
```

#### 7.2 Reports
```python
# tests/unit/ambiental/test_reports.py

class TestInformeAmbientalGenerator:
    - test_consolidar_datos
    - test_render_html
    - test_generar_pdf
    - test_generar_excel
    - test_calcular_area_intervenida
    - test_calcular_vegetacion
```

#### 7.3 Tasks
```python
# tests/unit/ambiental/test_tasks.py

class TestGenerarInformeAmbiental:
    - test_generates_pdf
    - test_saves_to_storage
    - test_updates_informe_record

class TestVerificarPermisosVencidos:
    - test_detects_expired
    - test_detects_expiring_soon
    - test_updates_status
```

---

### 8. Módulo: `financiero`

#### 8.1 Modelos
```python
# tests/unit/financiero/test_models.py

class TestPresupuestoModel:
    - test_create_presupuesto
    - test_presupuesto_por_linea_mes
    - test_porcentaje_ejecutado_property

class TestEjecucionCostoModel:
    - test_create_ejecucion
    - test_ejecucion_linked_to_actividad
    - test_costo_total_calculation
```

#### 8.2 Reports
```python
# tests/unit/financiero/test_reports.py

class TestCuadroCostosGenerator:
    - test_generar_excel
    - test_hoja_resumen
    - test_hoja_personal
    - test_hoja_vehiculos
    - test_totales_calculation
```

#### 8.3 Tasks
```python
# tests/unit/financiero/test_tasks.py

class TestCalcularCostosActividades:
    - test_calculates_personnel_cost
    - test_calculates_vehicle_cost
    - test_calculates_materials_cost

class TestGenerarCuadroCostos:
    - test_generates_monthly_report
    - test_saves_to_database
```

---

## Tests de Integración

### INT-001: Flujo Actividad → Campo → Indicadores

```python
# tests/integration/test_flujo_actividad.py

class TestFlujoActividadCompleto:
    """
    Flujo: Programar → Asignar → Iniciar → Registrar → Completar → Calcular KPI
    """

    - test_programar_actividad
        → Crear actividad con estado PENDIENTE
        → Asignar a cuadrilla
        → Verificar aparece en /mis-actividades

    - test_iniciar_actividad_crea_registro
        → POST /api/actividades/{id}/iniciar
        → Verificar RegistroCampo creado
        → Verificar estado cambia a EN_CURSO

    - test_subir_evidencias
        → POST /api/campo/{id}/evidencias
        → Verificar thumbnail generado
        → Verificar validación ejecutada

    - test_completar_actividad
        → POST /api/campo/{id}/finalizar
        → Verificar estado COMPLETADA
        → Verificar datos_formulario guardados

    - test_calculo_kpi_incluye_actividad
        → Ejecutar calcular_todos_indicadores
        → Verificar actividad cuenta en gestión
        → Verificar indicador actualizado
```

### INT-002: Flujo Ambiental

```python
# tests/integration/test_flujo_ambiental.py

class TestFlujoInformeAmbiental:
    """
    Flujo: Actividades completadas → Generar informe → PDF/Excel
    """

    - test_consolidar_actividades_mes
    - test_generar_informe_pdf
    - test_generar_informe_excel
    - test_enviar_informe_actualiza_estado
```

### INT-003: Flujo Financiero

```python
# tests/integration/test_flujo_financiero.py

class TestFlujoFacturacion:
    """
    Flujo: Actividades → Costos → Cuadro → Factura
    """

    - test_calcular_costos_actividades_completadas
    - test_generar_cuadro_costos_mensual
    - test_crear_ciclo_facturacion
```

### INT-004: Permisos y Roles

```python
# tests/integration/test_permisos.py

class TestPermisosRoles:
    """
    Verificar acceso por rol a cada módulo
    """

    - test_admin_acceso_total
    - test_director_acceso_dashboard
    - test_coordinador_acceso_programacion
    - test_liniero_solo_mis_actividades
    - test_ingeniero_residente_ver_indicadores
```

### INT-005: Sincronización Móvil

```python
# tests/integration/test_sync_movil.py

class TestSincronizacionOffline:
    """
    Simular operación offline y sync
    """

    - test_crear_registro_local
    - test_subir_evidencias_pendientes
    - test_sync_conflicto_resolucion
    - test_retry_on_network_error
```

---

## Tests E2E

### E2E-001: Jornada Completa Liniero

```python
# tests/e2e/test_jornada_liniero.py

class TestJornadaLiniero:
    """
    Simula día completo de trabajo de un liniero
    """

    def test_jornada_completa(self):
        # 1. Login
        response = client.post('/api/auth/login', credentials)
        assert response.status_code == 200
        token = response.json()['access']

        # 2. Ver actividades asignadas
        response = client.get('/api/actividades/mis-actividades',
                             headers={'Authorization': f'Bearer {token}'})
        actividades = response.json()
        assert len(actividades) > 0

        # 3. Iniciar primera actividad
        actividad_id = actividades[0]['id']
        response = client.post(f'/api/actividades/{actividad_id}/iniciar',
                              json={'latitud': 4.7110, 'longitud': -74.0721})
        registro_id = response.json()['registro_id']

        # 4. Subir fotos ANTES
        for i in range(3):
            response = client.post(f'/api/campo/{registro_id}/evidencias',
                                  files={'foto': crear_imagen_test()},
                                  data={'tipo': 'ANTES'})
            assert response.status_code == 201

        # 5. Subir fotos DURANTE
        # ... similar

        # 6. Subir fotos DESPUES y completar
        response = client.post(f'/api/campo/{registro_id}/finalizar',
                              json={'observaciones': 'Trabajo completado'})
        assert response.status_code == 200

        # 7. Verificar actividad completada
        response = client.get(f'/api/actividades/{actividad_id}')
        assert response.json()['estado'] == 'COMPLETADA'
```

### E2E-002: Generación Mensual de Reportes

```python
# tests/e2e/test_reportes_mensuales.py

class TestReportesMensuales:
    """
    Simula cierre de mes con generación de reportes
    """

    def test_cierre_mes_completo(self):
        # Setup: crear actividades del mes
        crear_actividades_mes_completo()

        # 1. Calcular indicadores
        resultados = calcular_todos_indicadores(linea.id, 2024, 1)
        assert len(resultados) == 6

        # 2. Generar informe ambiental
        generar_informe_ambiental(informe_id)
        informe.refresh_from_db()
        assert informe.archivo_pdf is not None

        # 3. Generar cuadro de costos
        generar_cuadro_costos_mensual(2024, 1)
        cuadro = CuadroCostos.objects.get(anio=2024, mes=1)
        assert cuadro.archivo is not None

        # 4. Verificar dashboard muestra datos
        response = client.get('/indicadores/dashboard/?mes=1&anio=2024')
        assert 'promedio_cumplimiento' in response.context
```

### E2E-003: Alerta de Permisos

```python
# tests/e2e/test_alertas_permisos.py

class TestAlertasPermisos:
    """
    Verifica sistema de alertas de permisos vencidos
    """

    def test_alerta_permiso_por_vencer(self):
        # Crear permiso que vence en 15 días
        permiso = crear_permiso_vencimiento(dias=15)

        # Ejecutar verificación
        alertas = verificar_permisos_vencidos()

        # Verificar alerta generada
        assert permiso.id in [p['permiso_id'] for p in alertas['por_vencer']]
```

---

## Criterios de Aceptación

### Cobertura Mínima

| Tipo | Objetivo | Mínimo Aceptable |
|------|----------|------------------|
| Líneas | 80% | 70% |
| Branches | 75% | 65% |
| Funciones | 85% | 75% |

### Tiempos de Ejecución

| Suite | Máximo |
|-------|--------|
| Unit tests | 60 segundos |
| Integration tests | 180 segundos |
| E2E tests | 300 segundos |
| **Total** | **10 minutos** |

### Comando de Ejecución

```bash
# Todos los tests
pytest

# Solo unitarios
pytest tests/unit/

# Solo integración
pytest tests/integration/

# Con cobertura
pytest --cov=apps --cov-report=html

# Tests paralelos
pytest -n auto
```

---

## Configuración CI

```yaml
# .github/workflows/tests.yml
- name: Run Tests
  run: |
    pytest --cov=apps --cov-report=xml -v

- name: Upload Coverage
  uses: codecov/codecov-action@v3
```
