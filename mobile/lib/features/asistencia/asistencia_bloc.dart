import 'package:equatable/equatable.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:uuid/uuid.dart';

import '../../core/constants.dart';
import '../../core/database/database.dart';

// Events
abstract class AsistenciaEvent extends Equatable {
  const AsistenciaEvent();

  @override
  List<Object?> get props => [];
}

class LoadMiembrosEvent extends AsistenciaEvent {}

class ChangeDateEvent extends AsistenciaEvent {
  final DateTime fecha;

  const ChangeDateEvent(this.fecha);

  @override
  List<Object?> get props => [fecha];
}

class UpdateAsistenciaEvent extends AsistenciaEvent {
  final String usuarioId;
  final String? tipoNovedad;
  final String? observacion;
  final String? horaEntrada;
  final String? horaSalida;

  const UpdateAsistenciaEvent({
    required this.usuarioId,
    this.tipoNovedad,
    this.observacion,
    this.horaEntrada,
    this.horaSalida,
  });

  @override
  List<Object?> get props => [usuarioId, tipoNovedad, observacion, horaEntrada, horaSalida];
}

class SaveAsistenciasEvent extends AsistenciaEvent {}

// States
abstract class AsistenciaState extends Equatable {
  const AsistenciaState();

  @override
  List<Object?> get props => [];
}

class AsistenciaInitial extends AsistenciaState {}

class AsistenciaLoading extends AsistenciaState {}

class AsistenciaLoaded extends AsistenciaState {
  final DateTime fecha;
  final List<CuadrillaMiembro> miembros;
  final Map<String, AsistenciaItem> asistencias;
  final bool hasChanges;
  final String? cuadrillaId;

  const AsistenciaLoaded({
    required this.fecha,
    required this.miembros,
    required this.asistencias,
    this.hasChanges = false,
    this.cuadrillaId,
  });

  AsistenciaItem? getAsistencia(String usuarioId) => asistencias[usuarioId];

  int countByTipo(String tipo) {
    return asistencias.values.where((a) => a.tipoNovedad == tipo).length;
  }

  int get countNovedades {
    return asistencias.values
        .where((a) => a.tipoNovedad != TipoNovedad.presente)
        .length;
  }

  AsistenciaLoaded copyWith({
    DateTime? fecha,
    List<CuadrillaMiembro>? miembros,
    Map<String, AsistenciaItem>? asistencias,
    bool? hasChanges,
    String? cuadrillaId,
  }) {
    return AsistenciaLoaded(
      fecha: fecha ?? this.fecha,
      miembros: miembros ?? this.miembros,
      asistencias: asistencias ?? this.asistencias,
      hasChanges: hasChanges ?? this.hasChanges,
      cuadrillaId: cuadrillaId ?? this.cuadrillaId,
    );
  }

  @override
  List<Object?> get props => [fecha, miembros, asistencias, hasChanges, cuadrillaId];
}

class AsistenciaSaved extends AsistenciaState {}

class AsistenciaError extends AsistenciaState {
  final String message;

  const AsistenciaError(this.message);

  @override
  List<Object?> get props => [message];
}

// Data class for asistencia item
class AsistenciaItem {
  final String? id;
  final String usuarioId;
  final String tipoNovedad;
  final String observacion;
  final String? horaEntrada;
  final String? horaSalida;
  final bool sincronizado;

  const AsistenciaItem({
    this.id,
    required this.usuarioId,
    this.tipoNovedad = TipoNovedad.presente,
    this.observacion = '',
    this.horaEntrada,
    this.horaSalida,
    this.sincronizado = false,
  });

  AsistenciaItem copyWith({
    String? id,
    String? usuarioId,
    String? tipoNovedad,
    String? observacion,
    String? horaEntrada,
    String? horaSalida,
    bool? sincronizado,
  }) {
    return AsistenciaItem(
      id: id ?? this.id,
      usuarioId: usuarioId ?? this.usuarioId,
      tipoNovedad: tipoNovedad ?? this.tipoNovedad,
      observacion: observacion ?? this.observacion,
      horaEntrada: horaEntrada ?? this.horaEntrada,
      horaSalida: horaSalida ?? this.horaSalida,
      sincronizado: sincronizado ?? this.sincronizado,
    );
  }
}

// Bloc
class AsistenciaBloc extends Bloc<AsistenciaEvent, AsistenciaState> {
  final AppDatabase database;
  final _uuid = const Uuid();

  AsistenciaBloc({required this.database}) : super(AsistenciaInitial()) {
    on<LoadMiembrosEvent>(_onLoadMiembros);
    on<ChangeDateEvent>(_onChangeDate);
    on<UpdateAsistenciaEvent>(_onUpdateAsistencia);
    on<SaveAsistenciasEvent>(_onSaveAsistencias);
  }

  Future<void> _onLoadMiembros(
    LoadMiembrosEvent event,
    Emitter<AsistenciaState> emit,
  ) async {
    emit(AsistenciaLoading());

    try {
      // TODO: Get cuadrillaId from current user session
      // For now, we'll get all miembros
      final miembros = await database.select(database.cuadrillaMiembros).get();

      if (miembros.isEmpty) {
        emit(const AsistenciaError('No hay miembros en la cuadrilla'));
        return;
      }

      final cuadrillaId = miembros.first.cuadrillaId;
      final fecha = DateTime.now();

      // Load existing asistencias for today
      final existingAsistencias = await database.getAsistenciasPorFecha(fecha);

      final asistenciasMap = <String, AsistenciaItem>{};

      // Initialize all miembros with PRESENTE by default
      for (final miembro in miembros) {
        final existing = existingAsistencias
            .cast<Asistencia?>()
            .firstWhere(
              (a) => a?.usuarioId == miembro.usuarioId,
              orElse: () => null,
            );

        if (existing != null) {
          asistenciasMap[miembro.usuarioId] = AsistenciaItem(
            id: existing.id,
            usuarioId: existing.usuarioId,
            tipoNovedad: existing.tipoNovedad,
            observacion: existing.observacion,
            horaEntrada: existing.horaEntrada,
            horaSalida: existing.horaSalida,
            sincronizado: existing.sincronizado,
          );
        } else {
          asistenciasMap[miembro.usuarioId] = AsistenciaItem(
            usuarioId: miembro.usuarioId,
          );
        }
      }

      emit(AsistenciaLoaded(
        fecha: fecha,
        miembros: miembros,
        asistencias: asistenciasMap,
        cuadrillaId: cuadrillaId,
      ));
    } catch (e) {
      emit(AsistenciaError('Error al cargar datos: $e'));
    }
  }

  Future<void> _onChangeDate(
    ChangeDateEvent event,
    Emitter<AsistenciaState> emit,
  ) async {
    final currentState = state;
    if (currentState is! AsistenciaLoaded) return;

    emit(AsistenciaLoading());

    try {
      // Load asistencias for the new date
      final existingAsistencias = await database.getAsistenciasPorFecha(event.fecha);

      final asistenciasMap = <String, AsistenciaItem>{};

      for (final miembro in currentState.miembros) {
        final existing = existingAsistencias
            .cast<Asistencia?>()
            .firstWhere(
              (a) => a?.usuarioId == miembro.usuarioId,
              orElse: () => null,
            );

        if (existing != null) {
          asistenciasMap[miembro.usuarioId] = AsistenciaItem(
            id: existing.id,
            usuarioId: existing.usuarioId,
            tipoNovedad: existing.tipoNovedad,
            observacion: existing.observacion,
            horaEntrada: existing.horaEntrada,
            horaSalida: existing.horaSalida,
            sincronizado: existing.sincronizado,
          );
        } else {
          asistenciasMap[miembro.usuarioId] = AsistenciaItem(
            usuarioId: miembro.usuarioId,
          );
        }
      }

      emit(currentState.copyWith(
        fecha: event.fecha,
        asistencias: asistenciasMap,
        hasChanges: false,
      ));
    } catch (e) {
      emit(AsistenciaError('Error al cambiar fecha: $e'));
    }
  }

  void _onUpdateAsistencia(
    UpdateAsistenciaEvent event,
    Emitter<AsistenciaState> emit,
  ) {
    final currentState = state;
    if (currentState is! AsistenciaLoaded) return;

    final currentAsistencia = currentState.asistencias[event.usuarioId];
    if (currentAsistencia == null) return;

    final updatedAsistencia = currentAsistencia.copyWith(
      tipoNovedad: event.tipoNovedad,
      observacion: event.observacion,
      horaEntrada: event.horaEntrada,
      horaSalida: event.horaSalida,
    );

    final newAsistencias = Map<String, AsistenciaItem>.from(currentState.asistencias);
    newAsistencias[event.usuarioId] = updatedAsistencia;

    emit(currentState.copyWith(
      asistencias: newAsistencias,
      hasChanges: true,
    ));
  }

  Future<void> _onSaveAsistencias(
    SaveAsistenciasEvent event,
    Emitter<AsistenciaState> emit,
  ) async {
    final currentState = state;
    if (currentState is! AsistenciaLoaded) return;

    try {
      final companions = <AsistenciasCompanion>[];

      for (final entry in currentState.asistencias.entries) {
        final item = entry.value;
        final miembro = currentState.miembros.firstWhere(
          (m) => m.usuarioId == item.usuarioId,
        );

        companions.add(AsistenciasCompanion.insert(
          id: item.id ?? _uuid.v4(),
          usuarioId: item.usuarioId,
          usuarioNombre: miembro.usuarioNombre,
          cuadrillaId: currentState.cuadrillaId ?? '',
          cuadrillaCodigo: miembro.cuadrillaId, // Using as codigo for now
          fecha: currentState.fecha,
          tipoNovedad: Value(item.tipoNovedad),
          horaEntrada: Value(item.horaEntrada),
          horaSalida: Value(item.horaSalida),
          observacion: Value(item.observacion),
          sincronizado: const Value(false),
          createdAt: DateTime.now(),
        ));
      }

      await database.insertAsistencias(companions);

      // Add to sync queue
      for (final companion in companions) {
        await database.addToSyncQueue(SyncQueueCompanion.insert(
          tipo: 'asistencia',
          entidadId: companion.id.value,
          datos: '{}', // Will be populated by sync manager
          createdAt: DateTime.now(),
        ));
      }

      emit(currentState.copyWith(hasChanges: false));
    } catch (e) {
      emit(AsistenciaError('Error al guardar: $e'));
    }
  }
}
