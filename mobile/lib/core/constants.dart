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
  static const int dbVersion = 1;

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
