import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:pretty_dio_logger/pretty_dio_logger.dart';

import '../constants.dart';
import 'interceptors.dart';

class ApiClient {
  late final Dio _dio;
  final FlutterSecureStorage _storage;

  ApiClient(this._storage) {
    _dio = Dio(
      BaseOptions(
        baseUrl: AppConstants.apiBaseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 30),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    _dio.interceptors.addAll([
      AuthInterceptor(_storage, _dio),
      PrettyDioLogger(
        requestHeader: true,
        requestBody: true,
        responseBody: true,
        responseHeader: false,
        compact: true,
      ),
    ]);
  }

  Dio get dio => _dio;

  // Auth endpoints
  Future<Response> login(String email, String password) async {
    return _dio.post('/auth/login', data: {
      'email': email,
      'password': password,
    });
  }

  Future<Response> refreshToken(String refreshToken) async {
    return _dio.post('/auth/refresh', data: {
      'refresh': refreshToken,
    });
  }

  Future<Response> getMe() async {
    return _dio.get('/auth/me');
  }

  // Activities endpoints
  Future<Response> getMisActividades({String? fecha}) async {
    return _dio.get('/actividades/mis-actividades', queryParameters: {
      if (fecha != null) 'fecha': fecha,
    });
  }

  Future<Response> iniciarActividad(String actividadId, double lat, double lon) async {
    return _dio.post('/actividades/$actividadId/iniciar', data: {
      'lat': lat,
      'lon': lon,
    });
  }

  // Field records endpoints
  Future<Response> syncRegistros(List<Map<String, dynamic>> registros) async {
    return _dio.post('/campo/registros/sync', data: {
      'registros': registros,
    });
  }

  Future<Response> uploadEvidencia(
    String registroId,
    String tipo,
    double lat,
    double lon,
    DateTime fechaCaptura,
    List<int> imageBytes,
    String fileName,
  ) async {
    final formData = FormData.fromMap({
      'registro_id': registroId,
      'tipo': tipo,
      'lat': lat,
      'lon': lon,
      'fecha_captura': fechaCaptura.toIso8601String(),
      'archivo': MultipartFile.fromBytes(imageBytes, filename: fileName),
    });

    return _dio.post('/campo/evidencias/upload', data: formData);
  }

  // Lines endpoints
  Future<Response> getLineas() async {
    return _dio.get('/lineas/');
  }

  Future<Response> getTorres(String lineaId) async {
    return _dio.get('/lineas/$lineaId/torres');
  }

  Future<Response> validarUbicacion(String torreId, double lat, double lon) async {
    return _dio.post('/lineas/validar-ubicacion', data: {
      'torre_id': torreId,
      'lat': lat,
      'lon': lon,
    });
  }
}
