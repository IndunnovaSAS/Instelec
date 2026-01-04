import 'dart:async';
import 'dart:convert';

import 'package:connectivity_plus/connectivity_plus.dart';

import '../api/api_client.dart';
import '../database/database.dart';

enum SyncStatus { idle, syncing, completed, error }

class SyncManager {
  final AppDatabase _db;
  final ApiClient _api;

  SyncStatus _status = SyncStatus.idle;
  String? _lastError;
  DateTime? _lastSyncTime;

  final _statusController = StreamController<SyncStatus>.broadcast();

  SyncManager(this._db, this._api);

  SyncStatus get status => _status;
  String? get lastError => _lastError;
  DateTime? get lastSyncTime => _lastSyncTime;
  Stream<SyncStatus> get statusStream => _statusController.stream;

  /// Check if device is online
  Future<bool> isOnline() async {
    final result = await Connectivity().checkConnectivity();
    return !result.contains(ConnectivityResult.none);
  }

  /// Perform full sync
  Future<void> sync() async {
    if (_status == SyncStatus.syncing) return;

    final online = await isOnline();
    if (!online) {
      _lastError = 'Sin conexión a internet';
      return;
    }

    _setStatus(SyncStatus.syncing);

    try {
      // 1. Download new activities
      await _downloadActividades();

      // 2. Upload pending records
      await _uploadRegistros();

      // 3. Upload pending evidence photos
      await _uploadEvidencias();

      // 4. Process sync queue
      await _processSyncQueue();

      _lastSyncTime = DateTime.now();
      _lastError = null;
      _setStatus(SyncStatus.completed);
    } catch (e) {
      _lastError = e.toString();
      _setStatus(SyncStatus.error);
      rethrow;
    }
  }

  /// Download activities from server
  Future<void> _downloadActividades() async {
    final response = await _api.getMisActividades();

    if (response.statusCode == 200) {
      final List<dynamic> data = response.data;

      final actividades = data.map((item) => ActividadesCompanion.insert(
            id: item['id'],
            lineaCodigo: item['linea_codigo'],
            lineaNombre: item['linea_nombre'],
            torreNumero: item['torre_numero'],
            torreLatitud: item['torre_latitud'],
            torreLongitud: item['torre_longitud'],
            tipoActividad: item['tipo_actividad_nombre'],
            categoria: item['tipo_actividad_categoria'],
            fechaProgramada: DateTime.parse(item['fecha_programada']),
            estado: item['estado'],
            prioridad: item['prioridad'],
            camposFormulario: Value(jsonEncode(item['campos_formulario'])),
          )).toList();

      await _db.insertActividades(actividades);
    }
  }

  /// Upload pending field records
  Future<void> _uploadRegistros() async {
    final registros = await _db.getRegistrosNoSincronizados();

    if (registros.isEmpty) return;

    final registrosData = registros.map((r) => {
          'actividad_id': r.actividadId,
          'datos_formulario': jsonDecode(r.datosFormulario),
          'observaciones': r.observaciones,
          'latitud_fin': r.latitudFin,
          'longitud_fin': r.longitudFin,
          'fecha_fin': r.fechaFin?.toIso8601String(),
        }).toList();

    final response = await _api.syncRegistros(registrosData);

    if (response.statusCode == 200) {
      final resultados = response.data['resultados'] as List;
      for (var i = 0; i < resultados.length; i++) {
        if (resultados[i]['status'] == 'ok') {
          await _db.marcarRegistroSincronizado(registros[i].id);
        }
      }
    }
  }

  /// Upload pending evidence photos
  Future<void> _uploadEvidencias() async {
    final evidencias = await _db.getEvidenciasNoSincronizadas();

    for (final evidencia in evidencias) {
      try {
        // Read file from local path
        final file = File(evidencia.rutaLocal);
        if (!await file.exists()) continue;

        final bytes = await file.readAsBytes();

        final response = await _api.uploadEvidencia(
          evidencia.registroId,
          evidencia.tipo,
          evidencia.latitud ?? 0,
          evidencia.longitud ?? 0,
          evidencia.fechaCaptura,
          bytes,
          '${evidencia.id}.jpg',
        );

        if (response.statusCode == 200) {
          await _db.marcarEvidenciaSincronizada(
            evidencia.id,
            response.data['url'],
          );
        }
      } catch (e) {
        // Add to sync queue for retry
        await _db.addToSyncQueue(SyncQueueCompanion.insert(
          tipo: 'evidencia',
          entidadId: evidencia.id,
          datos: jsonEncode({'path': evidencia.rutaLocal}),
          createdAt: DateTime.now(),
        ));
      }
    }
  }

  /// Process items in sync queue
  Future<void> _processSyncQueue() async {
    final items = await _db.getPendingSync();

    for (final item in items) {
      try {
        // Process based on type
        if (item.tipo == 'evidencia') {
          // Retry evidence upload
          final data = jsonDecode(item.datos);
          // ... implement retry logic
        }

        await _db.removeSyncItem(item.id);
      } catch (e) {
        await _db.incrementSyncAttempt(item.id, e.toString());
      }
    }
  }

  void _setStatus(SyncStatus status) {
    _status = status;
    _statusController.add(status);
  }

  void dispose() {
    _statusController.close();
  }
}

// Need to import dart:io for File
import 'dart:io';
