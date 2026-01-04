import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import '../constants.dart';

class AuthInterceptor extends Interceptor {
  final FlutterSecureStorage _storage;
  final Dio _dio;

  AuthInterceptor(this._storage, this._dio);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) async {
    // Skip auth for login and refresh endpoints
    if (options.path.contains('/auth/login') ||
        options.path.contains('/auth/refresh')) {
      return handler.next(options);
    }

    final accessToken = await _storage.read(key: AppConstants.accessTokenKey);
    if (accessToken != null) {
      options.headers['Authorization'] = 'Bearer $accessToken';
    }

    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode == 401) {
      // Try to refresh token
      final refreshToken = await _storage.read(key: AppConstants.refreshTokenKey);
      if (refreshToken != null) {
        try {
          final response = await _dio.post(
            '/auth/refresh',
            data: {'refresh': refreshToken},
          );

          if (response.statusCode == 200) {
            final newAccessToken = response.data['access'];
            await _storage.write(
              key: AppConstants.accessTokenKey,
              value: newAccessToken,
            );

            // Retry original request
            final opts = err.requestOptions;
            opts.headers['Authorization'] = 'Bearer $newAccessToken';
            final retryResponse = await _dio.fetch(opts);
            return handler.resolve(retryResponse);
          }
        } catch (e) {
          // Refresh failed, clear tokens
          await _storage.delete(key: AppConstants.accessTokenKey);
          await _storage.delete(key: AppConstants.refreshTokenKey);
        }
      }
    }

    handler.next(err);
  }
}
