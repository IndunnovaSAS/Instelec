class AppConstants {
  // API Configuration
  static const String apiBaseUrl = 'https://api.transmaint.instelec.com.co/api/v1';
  static const String devApiBaseUrl = 'http://localhost:8000/api/v1';

  // Storage Keys
  static const String accessTokenKey = 'access_token';
  static const String refreshTokenKey = 'refresh_token';
  static const String userDataKey = 'user_data';

  // Database
  static const String dbName = 'transmaint.db';
  static const int dbVersion = 2; // Updated for avance, pendientes, asistencia tables

  // Sync Configuration
  static const int syncIntervalMinutes = 15;
  static const int maxRetryAttempts = 3;
  static const int retryDelaySeconds = 30;

  // Photo Configuration
  static const int maxPhotoWidth = 1920;
  static const int maxPhotoHeight = 1080;
  static const int photoQuality = 85;
  static const int thumbnailSize = 400;

  // Location Configuration
  static const int locationTimeoutSeconds = 30;
  static const double locationAccuracyThreshold = 50.0; // meters
  static const double polygonValidationRadius = 100.0; // meters

  // ML Model
  static const String photoValidatorModel = 'assets/ml/photo_validator.tflite';
  static const double photoValidationThreshold = 0.8;
}

/// Tipos de pendiente para registros de campo
class TipoPendiente {
  static const String acceso = 'ACCESO';
  static const String permisos = 'PERMISOS';
  static const String clima = 'CLIMA';
  static const String material = 'MATERIAL';
  static const String equipo = 'EQUIPO';
  static const String seguridad = 'SEGURIDAD';
  static const String propietario = 'PROPIETARIO';
  static const String otro = 'OTRO';

  static const Map<String, String> displayNames = {
    acceso: 'Problema de acceso',
    permisos: 'Falta de permisos',
    clima: 'Condiciones climáticas',
    material: 'Falta de material',
    equipo: 'Falta de equipo',
    seguridad: 'Condición de seguridad',
    propietario: 'Problema con propietario',
    otro: 'Otro',
  };

  static List<String> get values => displayNames.keys.toList();
}

/// Tipos de novedad para asistencia
class TipoNovedad {
  static const String presente = 'PRESENTE';
  static const String vacaciones = 'VACACIONES';
  static const String incapacidad = 'INCAPACIDAD';
  static const String permiso = 'PERMISO';
  static const String ausente = 'AUSENTE';
  static const String licencia = 'LICENCIA';
  static const String capacitacion = 'CAPACITACION';

  static const Map<String, String> displayNames = {
    presente: 'Presente',
    vacaciones: 'Vacaciones',
    incapacidad: 'Incapacidad',
    permiso: 'Permiso',
    ausente: 'Ausente',
    licencia: 'Licencia',
    capacitacion: 'Capacitación',
  };

  static List<String> get values => displayNames.keys.toList();
}
