import 'package:flutter/material.dart';

import '../../../../core/constants.dart';

/// Widget de formulario para registrar pendientes/condiciones especiales
class AvancePendienteForm extends StatelessWidget {
  final bool tienePendiente;
  final String tipoPendiente;
  final String descripcionPendiente;
  final ValueChanged<bool> onTienePendienteChanged;
  final ValueChanged<String?> onTipoPendienteChanged;
  final ValueChanged<String> onDescripcionChanged;

  const AvancePendienteForm({
    super.key,
    required this.tienePendiente,
    required this.tipoPendiente,
    required this.descripcionPendiente,
    required this.onTienePendienteChanged,
    required this.onTipoPendienteChanged,
    required this.onDescripcionChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header con switch
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Row(
                  children: [
                    Icon(
                      Icons.warning_amber_rounded,
                      color: tienePendiente ? Colors.orange : Colors.grey,
                    ),
                    const SizedBox(width: 8),
                    Text(
                      'Pendiente / Condición Especial',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                  ],
                ),
                Switch(
                  value: tienePendiente,
                  onChanged: onTienePendienteChanged,
                  activeColor: Colors.orange,
                ),
              ],
            ),

            // Campos adicionales cuando hay pendiente
            if (tienePendiente) ...[
              const SizedBox(height: 16),
              const Text(
                'Marque esta opción si existe alguna condición que impida '
                'completar la actividad o requiera atención especial.',
                style: TextStyle(
                  fontSize: 12,
                  color: Colors.grey,
                ),
              ),
              const SizedBox(height: 16),

              // Tipo de pendiente
              DropdownButtonFormField<String>(
                value: tipoPendiente.isNotEmpty ? tipoPendiente : null,
                decoration: const InputDecoration(
                  labelText: 'Tipo de Pendiente',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.category),
                ),
                hint: const Text('Seleccione el tipo'),
                items: TipoPendiente.displayNames.entries
                    .map((e) => DropdownMenuItem(
                          value: e.key,
                          child: Text(e.value),
                        ))
                    .toList(),
                onChanged: onTipoPendienteChanged,
                validator: (value) {
                  if (tienePendiente && (value == null || value.isEmpty)) {
                    return 'Seleccione el tipo de pendiente';
                  }
                  return null;
                },
              ),
              const SizedBox(height: 16),

              // Descripción del pendiente
              TextFormField(
                initialValue: descripcionPendiente,
                decoration: const InputDecoration(
                  labelText: 'Descripción del Pendiente',
                  border: OutlineInputBorder(),
                  prefixIcon: Icon(Icons.description),
                  hintText: 'Describa la condición o pendiente...',
                ),
                maxLines: 3,
                onChanged: onDescripcionChanged,
                validator: (value) {
                  if (tienePendiente && (value == null || value.isEmpty)) {
                    return 'Describa el pendiente';
                  }
                  return null;
                },
              ),

              const SizedBox(height: 12),

              // Información adicional
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Colors.orange.shade50,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: Colors.orange.shade200),
                ),
                child: Row(
                  children: [
                    Icon(Icons.info_outline, color: Colors.orange.shade700),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        'Este pendiente será reportado y se incluirá en el '
                        'reporte de condiciones especiales.',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.orange.shade900,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }
}

/// Widget para mostrar chips de tipo de pendiente (vista resumida)
class TipoPendienteChip extends StatelessWidget {
  final String tipo;
  final bool selected;
  final VoidCallback? onTap;

  const TipoPendienteChip({
    super.key,
    required this.tipo,
    this.selected = false,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final displayName = TipoPendiente.displayNames[tipo] ?? tipo;
    final color = _getColorForTipo(tipo);

    return ActionChip(
      label: Text(displayName),
      avatar: Icon(
        _getIconForTipo(tipo),
        size: 18,
        color: selected ? Colors.white : color,
      ),
      backgroundColor: selected ? color : color.withOpacity(0.1),
      labelStyle: TextStyle(
        color: selected ? Colors.white : color,
        fontWeight: selected ? FontWeight.bold : FontWeight.normal,
      ),
      onPressed: onTap,
    );
  }

  Color _getColorForTipo(String tipo) {
    switch (tipo) {
      case TipoPendiente.acceso:
        return Colors.red;
      case TipoPendiente.permisos:
        return Colors.purple;
      case TipoPendiente.clima:
        return Colors.blue;
      case TipoPendiente.material:
        return Colors.brown;
      case TipoPendiente.equipo:
        return Colors.teal;
      case TipoPendiente.seguridad:
        return Colors.orange;
      case TipoPendiente.propietario:
        return Colors.indigo;
      default:
        return Colors.grey;
    }
  }

  IconData _getIconForTipo(String tipo) {
    switch (tipo) {
      case TipoPendiente.acceso:
        return Icons.no_encryption;
      case TipoPendiente.permisos:
        return Icons.gavel;
      case TipoPendiente.clima:
        return Icons.cloud;
      case TipoPendiente.material:
        return Icons.inventory_2;
      case TipoPendiente.equipo:
        return Icons.build;
      case TipoPendiente.seguridad:
        return Icons.security;
      case TipoPendiente.propietario:
        return Icons.person_off;
      default:
        return Icons.warning;
    }
  }
}
