import 'dart:io';

import 'package:drift/drift.dart';
import 'package:drift/native.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as p;

import '../constants.dart';

part 'database.g.dart';

// Tables
class Actividades extends Table {
  TextColumn get id => text()();
  TextColumn get lineaCodigo => text()();
  TextColumn get lineaNombre => text()();
  TextColumn get torreNumero => text()();
  RealColumn get torreLatitud => real()();
  RealColumn get torreLongitud => real()();
  TextColumn get tipoActividad => text()();
  TextColumn get categoria => text()();
  DateTimeColumn get fechaProgramada => dateTime()();
  TextColumn get estado => text()();
  TextColumn get prioridad => text()();
  TextColumn get camposFormulario => text().nullable()();
  BoolColumn get sincronizado => boolean().withDefault(const Constant(false))();
  DateTimeColumn get updatedAt => dateTime().nullable()();
  // New fields for Transelca integration
  TextColumn get avisoSap => text().withDefault(const Constant(''))();
  RealColumn get porcentajeAvance => real().withDefault(const Constant(0.0))();
  RealColumn get valorFacturacion => real().withDefault(const Constant(0.0))();
  TextColumn get tramoCodigo => text().nullable()();
  TextColumn get tramoNombre => text().nullable()();

  @override
  Set<Column> get primaryKey => {id};
}

class RegistrosCampo extends Table {
  TextColumn get id => text()();
  TextColumn get actividadId => text().references(Actividades, #id)();
  TextColumn get usuarioId => text()();
  DateTimeColumn get fechaInicio => dateTime()();
  DateTimeColumn get fechaFin => dateTime().nullable()();
  RealColumn get latitudInicio => real().nullable()();
  RealColumn get longitudInicio => real().nullable()();
  RealColumn get latitudFin => real().nullable()();
  RealColumn get longitudFin => real().nullable()();
  BoolColumn get dentroPoligono => boolean().nullable()();
  TextColumn get datosFormulario => text().withDefault(const Constant('{}'))();
  TextColumn get observaciones => text().withDefault(const Constant(''))();
  BoolColumn get sincronizado => boolean().withDefault(const Constant(false))();
  DateTimeColumn get createdAt => dateTime()();
  // New fields for avance and pendientes
  RealColumn get porcentajeAvanceReportado => real().withDefault(const Constant(0.0))();
  BoolColumn get tienePendiente => boolean().withDefault(const Constant(false))();
  TextColumn get tipoPendiente => text().withDefault(const Constant(''))();
  TextColumn get descripcionPendiente => text().withDefault(const Constant(''))();

  @override
  Set<Column> get primaryKey => {id};
}

class Evidencias extends Table {
  TextColumn get id => text()();
  TextColumn get registroId => text().references(RegistrosCampo, #id)();
  TextColumn get tipo => text()(); // ANTES, DURANTE, DESPUES
  TextColumn get rutaLocal => text()();
  TextColumn get urlRemota => text().nullable()();
  RealColumn get latitud => real().nullable()();
  RealColumn get longitud => real().nullable()();
  DateTimeColumn get fechaCaptura => dateTime()();
  TextColumn get validacionIa => text().nullable()();
  BoolColumn get sincronizado => boolean().withDefault(const Constant(false))();

  @override
  Set<Column> get primaryKey => {id};
}

class SyncQueue extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get tipo => text()(); // registro, evidencia, asistencia
  TextColumn get entidadId => text()();
  TextColumn get datos => text()();
  IntColumn get intentos => integer().withDefault(const Constant(0))();
  TextColumn get error => text().nullable()();
  DateTimeColumn get createdAt => dateTime()();
  DateTimeColumn get lastAttempt => dateTime().nullable()();
}

/// Asistencia diaria del personal de cuadrillas
class Asistencias extends Table {
  TextColumn get id => text()();
  TextColumn get usuarioId => text()();
  TextColumn get usuarioNombre => text()();
  TextColumn get cuadrillaId => text()();
  TextColumn get cuadrillaCodigo => text()();
  DateTimeColumn get fecha => dateTime()();
  TextColumn get tipoNovedad => text().withDefault(const Constant('PRESENTE'))();
  TextColumn get horaEntrada => text().nullable()(); // Stored as HH:mm string
  TextColumn get horaSalida => text().nullable()(); // Stored as HH:mm string
  TextColumn get observacion => text().withDefault(const Constant(''))();
  BoolColumn get sincronizado => boolean().withDefault(const Constant(false))();
  DateTimeColumn get createdAt => dateTime()();

  @override
  Set<Column> get primaryKey => {id};
}

/// Miembros de cuadrilla (para mostrar en pantalla de asistencia)
class CuadrillaMiembros extends Table {
  TextColumn get id => text()();
  TextColumn get cuadrillaId => text()();
  TextColumn get usuarioId => text()();
  TextColumn get usuarioNombre => text()();
  TextColumn get usuarioCedula => text().nullable()();
  TextColumn get usuarioTelefono => text().nullable()();
  TextColumn get rolCuadrilla => text()();
  BoolColumn get activo => boolean().withDefault(const Constant(true))();

  @override
  Set<Column> get primaryKey => {id};
}

@DriftDatabase(tables: [
  Actividades,
  RegistrosCampo,
  Evidencias,
  SyncQueue,
  Asistencias,
  CuadrillaMiembros,
])
class AppDatabase extends _$AppDatabase {
  AppDatabase() : super(_openConnection());

  @override
  int get schemaVersion => AppConstants.dbVersion;

  // Actividades queries
  Future<List<Actividade>> getActividades() => select(actividades).get();

  Future<List<Actividade>> getActividadesPendientes() {
    return (select(actividades)
          ..where((a) => a.estado.isIn(['PENDIENTE', 'EN_CURSO'])))
        .get();
  }

  Future<Actividade?> getActividad(String id) {
    return (select(actividades)..where((a) => a.id.equals(id))).getSingleOrNull();
  }

  Future<void> insertActividades(List<ActividadesCompanion> items) async {
    await batch((batch) {
      batch.insertAllOnConflictUpdate(actividades, items);
    });
  }

  // RegistrosCampo queries
  Future<List<RegistrosCampoData>> getRegistrosNoSincronizados() {
    return (select(registrosCampo)..where((r) => r.sincronizado.equals(false))).get();
  }

  Future<void> insertRegistro(RegistrosCampoCompanion registro) {
    return into(registrosCampo).insertOnConflictUpdate(registro);
  }

  Future<void> marcarRegistroSincronizado(String id) {
    return (update(registrosCampo)..where((r) => r.id.equals(id)))
        .write(const RegistrosCampoCompanion(sincronizado: Value(true)));
  }

  // Evidencias queries
  Future<List<Evidencia>> getEvidenciasNoSincronizadas() {
    return (select(evidencias)..where((e) => e.sincronizado.equals(false))).get();
  }

  Future<void> insertEvidencia(EvidenciasCompanion evidencia) {
    return into(evidencias).insertOnConflictUpdate(evidencia);
  }

  Future<void> marcarEvidenciaSincronizada(String id, String urlRemota) {
    return (update(evidencias)..where((e) => e.id.equals(id)))
        .write(EvidenciasCompanion(
          sincronizado: const Value(true),
          urlRemota: Value(urlRemota),
        ));
  }

  // SyncQueue queries
  Future<List<SyncQueueData>> getPendingSync() {
    return (select(syncQueue)
          ..where((s) => s.intentos.isSmallerThan(const Variable(AppConstants.maxRetryAttempts)))
          ..orderBy([(s) => OrderingTerm.asc(s.createdAt)]))
        .get();
  }

  Future<void> addToSyncQueue(SyncQueueCompanion item) {
    return into(syncQueue).insert(item);
  }

  Future<void> removeSyncItem(int id) {
    return (delete(syncQueue)..where((s) => s.id.equals(id))).go();
  }

  Future<void> incrementSyncAttempt(int id, String? error) {
    return (update(syncQueue)..where((s) => s.id.equals(id))).write(
      SyncQueueCompanion(
        intentos: syncQueue.intentos + const Variable(1),
        error: Value(error),
        lastAttempt: Value(DateTime.now()),
      ),
    );
  }

  // Asistencias queries
  Future<List<Asistencia>> getAsistenciasPorFecha(DateTime fecha) {
    final startOfDay = DateTime(fecha.year, fecha.month, fecha.day);
    final endOfDay = startOfDay.add(const Duration(days: 1));
    return (select(asistencias)
          ..where((a) =>
              a.fecha.isBiggerOrEqualValue(startOfDay) &
              a.fecha.isSmallerThanValue(endOfDay)))
        .get();
  }

  Future<List<Asistencia>> getAsistenciasNoSincronizadas() {
    return (select(asistencias)..where((a) => a.sincronizado.equals(false)))
        .get();
  }

  Future<void> insertAsistencia(AsistenciasCompanion asistencia) {
    return into(asistencias).insertOnConflictUpdate(asistencia);
  }

  Future<void> marcarAsistenciaSincronizada(String id) {
    return (update(asistencias)..where((a) => a.id.equals(id)))
        .write(const AsistenciasCompanion(sincronizado: Value(true)));
  }

  Future<void> insertAsistencias(List<AsistenciasCompanion> items) async {
    await batch((batch) {
      batch.insertAllOnConflictUpdate(asistencias, items);
    });
  }

  // CuadrillaMiembros queries
  Future<List<CuadrillaMiembro>> getMiembrosCuadrilla(String cuadrillaId) {
    return (select(cuadrillaMiembros)
          ..where((m) => m.cuadrillaId.equals(cuadrillaId) & m.activo.equals(true)))
        .get();
  }

  Future<void> insertMiembrosCuadrilla(List<CuadrillaMiembrosCompanion> items) async {
    await batch((batch) {
      batch.insertAllOnConflictUpdate(cuadrillaMiembros, items);
    });
  }

  // Update registro with avance and pendientes
  Future<void> updateRegistroAvance(
    String id, {
    required double porcentajeAvance,
    required bool tienePendiente,
    String? tipoPendiente,
    String? descripcionPendiente,
  }) {
    return (update(registrosCampo)..where((r) => r.id.equals(id))).write(
      RegistrosCampoCompanion(
        porcentajeAvanceReportado: Value(porcentajeAvance),
        tienePendiente: Value(tienePendiente),
        tipoPendiente: Value(tipoPendiente ?? ''),
        descripcionPendiente: Value(descripcionPendiente ?? ''),
      ),
    );
  }

  // Update actividad avance (after sync)
  Future<void> updateActividadAvance(String id, double porcentajeAvance) {
    return (update(actividades)..where((a) => a.id.equals(id))).write(
      ActividadesCompanion(
        porcentajeAvance: Value(porcentajeAvance),
        updatedAt: Value(DateTime.now()),
      ),
    );
  }
}

LazyDatabase _openConnection() {
  return LazyDatabase(() async {
    final dbFolder = await getApplicationDocumentsDirectory();
    final file = File(p.join(dbFolder.path, AppConstants.dbName));
    return NativeDatabase.createInBackground(file);
  });
}
