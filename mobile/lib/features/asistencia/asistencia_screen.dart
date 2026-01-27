import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:intl/intl.dart';

import '../../core/constants.dart';
import '../../core/database/database.dart';
import 'asistencia_bloc.dart';

/// Pantalla para marcar asistencia diaria de los miembros de la cuadrilla
class AsistenciaScreen extends StatelessWidget {
  const AsistenciaScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (context) => AsistenciaBloc(
        database: context.read<AppDatabase>(),
      )..add(LoadMiembrosEvent()),
      child: const _AsistenciaView(),
    );
  }
}

class _AsistenciaView extends StatelessWidget {
  const _AsistenciaView();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Asistencia'),
        actions: [
          BlocBuilder<AsistenciaBloc, AsistenciaState>(
            builder: (context, state) {
              if (state is AsistenciaLoaded) {
                return IconButton(
                  icon: const Icon(Icons.calendar_today),
                  onPressed: () => _selectDate(context, state.fecha),
                );
              }
              return const SizedBox.shrink();
            },
          ),
        ],
      ),
      body: BlocBuilder<AsistenciaBloc, AsistenciaState>(
        builder: (context, state) {
          if (state is AsistenciaLoading) {
            return const Center(child: CircularProgressIndicator());
          }

          if (state is AsistenciaError) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Icon(Icons.error_outline, size: 48, color: Colors.red),
                  const SizedBox(height: 16),
                  Text(state.message),
                  const SizedBox(height: 16),
                  ElevatedButton(
                    onPressed: () {
                      context.read<AsistenciaBloc>().add(LoadMiembrosEvent());
                    },
                    child: const Text('Reintentar'),
                  ),
                ],
              ),
            );
          }

          if (state is AsistenciaLoaded) {
            return _buildContent(context, state);
          }

          return const SizedBox.shrink();
        },
      ),
      floatingActionButton: BlocBuilder<AsistenciaBloc, AsistenciaState>(
        builder: (context, state) {
          if (state is AsistenciaLoaded && state.hasChanges) {
            return FloatingActionButton.extended(
              onPressed: () {
                context.read<AsistenciaBloc>().add(SaveAsistenciasEvent());
              },
              icon: const Icon(Icons.save),
              label: const Text('Guardar'),
            );
          }
          return const SizedBox.shrink();
        },
      ),
    );
  }

  Widget _buildContent(BuildContext context, AsistenciaLoaded state) {
    final dateFormat = DateFormat('EEEE, d MMMM yyyy', 'es');

    return Column(
      children: [
        // Header con fecha
        Container(
          padding: const EdgeInsets.all(16),
          color: Theme.of(context).colorScheme.primaryContainer,
          child: Row(
            children: [
              Icon(
                Icons.calendar_today,
                color: Theme.of(context).colorScheme.onPrimaryContainer,
              ),
              const SizedBox(width: 12),
              Text(
                dateFormat.format(state.fecha),
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: Theme.of(context).colorScheme.onPrimaryContainer,
                    ),
              ),
            ],
          ),
        ),

        // Resumen
        Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              _buildResumenCard(
                context,
                'Presentes',
                state.countByTipo(TipoNovedad.presente),
                Colors.green,
              ),
              const SizedBox(width: 8),
              _buildResumenCard(
                context,
                'Ausentes',
                state.countByTipo(TipoNovedad.ausente),
                Colors.red,
              ),
              const SizedBox(width: 8),
              _buildResumenCard(
                context,
                'Novedades',
                state.countNovedades,
                Colors.orange,
              ),
            ],
          ),
        ),

        // Lista de miembros
        Expanded(
          child: state.miembros.isEmpty
              ? const Center(
                  child: Text('No hay miembros en la cuadrilla'),
                )
              : ListView.builder(
                  itemCount: state.miembros.length,
                  padding: const EdgeInsets.symmetric(horizontal: 16),
                  itemBuilder: (context, index) {
                    final miembro = state.miembros[index];
                    final asistencia = state.getAsistencia(miembro.usuarioId);
                    return _MiembroAsistenciaCard(
                      miembro: miembro,
                      asistencia: asistencia,
                      onTipoChanged: (tipo) {
                        context.read<AsistenciaBloc>().add(
                              UpdateAsistenciaEvent(
                                usuarioId: miembro.usuarioId,
                                tipoNovedad: tipo,
                              ),
                            );
                      },
                      onObservacionChanged: (obs) {
                        context.read<AsistenciaBloc>().add(
                              UpdateAsistenciaEvent(
                                usuarioId: miembro.usuarioId,
                                observacion: obs,
                              ),
                            );
                      },
                    );
                  },
                ),
        ),
      ],
    );
  }

  Widget _buildResumenCard(
    BuildContext context,
    String label,
    int count,
    Color color,
  ) {
    return Expanded(
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            children: [
              Text(
                count.toString(),
                style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      color: color,
                      fontWeight: FontWeight.bold,
                    ),
              ),
              Text(
                label,
                style: Theme.of(context).textTheme.bodySmall,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _selectDate(BuildContext context, DateTime currentDate) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: currentDate,
      firstDate: DateTime.now().subtract(const Duration(days: 30)),
      lastDate: DateTime.now(),
      locale: const Locale('es'),
    );

    if (picked != null && context.mounted) {
      context.read<AsistenciaBloc>().add(ChangeDateEvent(picked));
    }
  }
}

class _MiembroAsistenciaCard extends StatelessWidget {
  final CuadrillaMiembro miembro;
  final AsistenciaItem? asistencia;
  final ValueChanged<String> onTipoChanged;
  final ValueChanged<String> onObservacionChanged;

  const _MiembroAsistenciaCard({
    required this.miembro,
    required this.asistencia,
    required this.onTipoChanged,
    required this.onObservacionChanged,
  });

  @override
  Widget build(BuildContext context) {
    final tipoNovedad = asistencia?.tipoNovedad ?? TipoNovedad.presente;
    final isPresente = tipoNovedad == TipoNovedad.presente;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Info del miembro
            Row(
              children: [
                CircleAvatar(
                  backgroundColor: isPresente ? Colors.green : Colors.orange,
                  child: Text(
                    miembro.usuarioNombre.isNotEmpty
                        ? miembro.usuarioNombre[0].toUpperCase()
                        : '?',
                    style: const TextStyle(color: Colors.white),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        miembro.usuarioNombre,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      Text(
                        '${miembro.rolCuadrilla} • ${miembro.usuarioCedula ?? ""}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
              ],
            ),

            const SizedBox(height: 16),

            // Selector de tipo de novedad
            DropdownButtonFormField<String>(
              value: tipoNovedad,
              decoration: const InputDecoration(
                labelText: 'Estado',
                border: OutlineInputBorder(),
                isDense: true,
              ),
              items: TipoNovedad.displayNames.entries
                  .map((e) => DropdownMenuItem(
                        value: e.key,
                        child: Text(e.value),
                      ))
                  .toList(),
              onChanged: (value) {
                if (value != null) {
                  onTipoChanged(value);
                }
              },
            ),

            // Campo de observación (solo si no es presente)
            if (!isPresente) ...[
              const SizedBox(height: 12),
              TextFormField(
                initialValue: asistencia?.observacion ?? '',
                decoration: const InputDecoration(
                  labelText: 'Observación',
                  border: OutlineInputBorder(),
                  isDense: true,
                ),
                maxLines: 2,
                onChanged: onObservacionChanged,
              ),
            ],
          ],
        ),
      ),
    );
  }
}
