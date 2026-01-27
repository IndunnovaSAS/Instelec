import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../../core/constants.dart';
import '../../../../core/database/database.dart';
import '../widgets/avance_pendiente_form.dart';

/// Pantalla de captura de datos de campo
/// Incluye:
/// - Formulario dinámico según tipo de actividad
/// - Campo de porcentaje de avance
/// - Opción de registrar pendientes/condiciones especiales
/// - Captura de evidencias fotográficas
class CapturaScreen extends StatefulWidget {
  final String actividadId;

  const CapturaScreen({super.key, required this.actividadId});

  @override
  State<CapturaScreen> createState() => _CapturaScreenState();
}

class _CapturaScreenState extends State<CapturaScreen> {
  final _formKey = GlobalKey<FormState>();
  final _observacionesController = TextEditingController();

  // Avance y pendientes
  double _porcentajeAvance = 0.0;
  bool _tienePendiente = false;
  String _tipoPendiente = '';
  String _descripcionPendiente = '';

  // Evidence counts
  int _fotosAntes = 0;
  int _fotosDurante = 0;
  int _fotosDespues = 0;

  Actividade? _actividad;
  bool _isLoading = true;
  bool _isSaving = false;

  @override
  void initState() {
    super.initState();
    _loadActividad();
  }

  Future<void> _loadActividad() async {
    final db = context.read<AppDatabase>();
    final actividad = await db.getActividad(widget.actividadId);
    if (mounted) {
      setState(() {
        _actividad = actividad;
        _porcentajeAvance = actividad?.porcentajeAvance ?? 0.0;
        _isLoading = false;
      });
    }
  }

  @override
  void dispose() {
    _observacionesController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Scaffold(
        body: Center(child: CircularProgressIndicator()),
      );
    }

    if (_actividad == null) {
      return Scaffold(
        appBar: AppBar(title: const Text('Error')),
        body: const Center(child: Text('Actividad no encontrada')),
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Text('Registro de Campo'),
        actions: [
          if (_isSaving)
            const Padding(
              padding: EdgeInsets.all(16),
              child: SizedBox(
                width: 24,
                height: 24,
                child: CircularProgressIndicator(strokeWidth: 2),
              ),
            )
          else
            IconButton(
              icon: const Icon(Icons.save),
              onPressed: _guardarRegistro,
            ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Info de actividad
            _buildActividadInfo(),
            const SizedBox(height: 24),

            // Porcentaje de avance
            _buildAvanceSection(),
            const SizedBox(height: 24),

            // Pendientes/Condiciones especiales
            AvancePendienteForm(
              tienePendiente: _tienePendiente,
              tipoPendiente: _tipoPendiente,
              descripcionPendiente: _descripcionPendiente,
              onTienePendienteChanged: (value) {
                setState(() => _tienePendiente = value);
              },
              onTipoPendienteChanged: (value) {
                setState(() => _tipoPendiente = value ?? '');
              },
              onDescripcionChanged: (value) {
                setState(() => _descripcionPendiente = value);
              },
            ),
            const SizedBox(height: 24),

            // Evidencias fotográficas
            _buildEvidenciasSection(),
            const SizedBox(height: 24),

            // Observaciones
            TextFormField(
              controller: _observacionesController,
              decoration: const InputDecoration(
                labelText: 'Observaciones',
                border: OutlineInputBorder(),
                hintText: 'Ingrese observaciones adicionales...',
              ),
              maxLines: 4,
            ),
            const SizedBox(height: 32),

            // Botón guardar
            ElevatedButton.icon(
              onPressed: _isSaving ? null : _guardarRegistro,
              icon: const Icon(Icons.save),
              label: const Text('Guardar Registro'),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.all(16),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildActividadInfo() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              _actividad!.tipoActividad,
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                const Icon(Icons.electric_bolt, size: 16),
                const SizedBox(width: 4),
                Text('${_actividad!.lineaCodigo} - ${_actividad!.lineaNombre}'),
              ],
            ),
            const SizedBox(height: 4),
            Row(
              children: [
                const Icon(Icons.cell_tower, size: 16),
                const SizedBox(width: 4),
                Text('Torre ${_actividad!.torreNumero}'),
              ],
            ),
            if (_actividad!.tramoCodigo != null) ...[
              const SizedBox(height: 4),
              Row(
                children: [
                  const Icon(Icons.route, size: 16),
                  const SizedBox(width: 4),
                  Text('Tramo: ${_actividad!.tramoNombre ?? _actividad!.tramoCodigo}'),
                ],
              ),
            ],
            if (_actividad!.avisoSap.isNotEmpty) ...[
              const SizedBox(height: 4),
              Row(
                children: [
                  const Icon(Icons.confirmation_number, size: 16),
                  const SizedBox(width: 4),
                  Text('Aviso SAP: ${_actividad!.avisoSap}'),
                ],
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildAvanceSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Porcentaje de Avance',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                  decoration: BoxDecoration(
                    color: _getAvanceColor(_porcentajeAvance),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    '${_porcentajeAvance.toStringAsFixed(0)}%',
                    style: const TextStyle(
                      color: Colors.white,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            Slider(
              value: _porcentajeAvance,
              min: 0,
              max: 100,
              divisions: 20,
              label: '${_porcentajeAvance.toStringAsFixed(0)}%',
              onChanged: (value) {
                setState(() => _porcentajeAvance = value);
              },
            ),
            const SizedBox(height: 8),
            // Quick select buttons
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [0, 25, 50, 75, 100].map((value) {
                final isSelected = _porcentajeAvance == value.toDouble();
                return ChoiceChip(
                  label: Text('$value%'),
                  selected: isSelected,
                  onSelected: (selected) {
                    if (selected) {
                      setState(() => _porcentajeAvance = value.toDouble());
                    }
                  },
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }

  Color _getAvanceColor(double avance) {
    if (avance >= 100) return Colors.green.shade700;
    if (avance >= 75) return Colors.green;
    if (avance >= 50) return Colors.orange;
    if (avance >= 25) return Colors.orange.shade700;
    return Colors.red;
  }

  Widget _buildEvidenciasSection() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Evidencias Fotográficas',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                Expanded(
                  child: _buildEvidenciaButton(
                    'ANTES',
                    _fotosAntes,
                    Icons.photo_camera_front,
                    Colors.blue,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _buildEvidenciaButton(
                    'DURANTE',
                    _fotosDurante,
                    Icons.photo_camera,
                    Colors.orange,
                  ),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _buildEvidenciaButton(
                    'DESPUES',
                    _fotosDespues,
                    Icons.photo_camera_back,
                    Colors.green,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEvidenciaButton(
    String tipo,
    int count,
    IconData icon,
    Color color,
  ) {
    return InkWell(
      onTap: () {
        context.push('/actividad/${widget.actividadId}/camera/${tipo.toLowerCase()}');
      },
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          border: Border.all(color: color.withOpacity(0.5)),
          borderRadius: BorderRadius.circular(12),
        ),
        child: Column(
          children: [
            Icon(icon, color: color, size: 32),
            const SizedBox(height: 8),
            Text(
              tipo,
              style: TextStyle(
                color: color,
                fontWeight: FontWeight.bold,
                fontSize: 12,
              ),
            ),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: count > 0 ? color : Colors.grey.shade300,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                '$count',
                style: TextStyle(
                  color: count > 0 ? Colors.white : Colors.grey.shade600,
                  fontSize: 12,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _guardarRegistro() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isSaving = true);

    try {
      final db = context.read<AppDatabase>();
      final now = DateTime.now();
      final registroId = DateTime.now().millisecondsSinceEpoch.toString();

      await db.insertRegistro(RegistrosCampoCompanion.insert(
        id: registroId,
        actividadId: widget.actividadId,
        usuarioId: 'current_user', // TODO: Get from auth
        fechaInicio: now,
        createdAt: now,
        observaciones: Value(_observacionesController.text),
        porcentajeAvanceReportado: Value(_porcentajeAvance),
        tienePendiente: Value(_tienePendiente),
        tipoPendiente: Value(_tipoPendiente),
        descripcionPendiente: Value(_descripcionPendiente),
      ));

      // Update actividad avance
      await db.updateActividadAvance(widget.actividadId, _porcentajeAvance);

      // Add to sync queue
      await db.addToSyncQueue(SyncQueueCompanion.insert(
        tipo: 'registro',
        entidadId: registroId,
        datos: '{}',
        createdAt: now,
      ));

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Registro guardado correctamente'),
            backgroundColor: Colors.green,
          ),
        );
        context.pop();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error al guardar: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isSaving = false);
      }
    }
  }
}
