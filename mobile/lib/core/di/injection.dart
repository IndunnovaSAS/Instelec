import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:get_it/get_it.dart';

import '../api/api_client.dart';
import '../database/database.dart';
import '../services/location_service.dart';
import '../services/camera_service.dart';
import '../services/photo_validator.dart';
import '../sync/sync_manager.dart';
import '../../features/auth/data/auth_repository.dart';
import '../../features/auth/presentation/bloc/auth_bloc.dart';
import '../../features/actividades/data/actividades_repository.dart';
import '../../features/actividades/presentation/bloc/actividades_bloc.dart';
import '../../features/captura/data/captura_repository.dart';
import '../../features/captura/presentation/bloc/captura_bloc.dart';
import '../../features/sync/data/sync_repository.dart';
import '../../features/sync/presentation/bloc/sync_bloc.dart';

final getIt = GetIt.instance;

Future<void> configureDependencies() async {
  // Core
  getIt.registerLazySingleton<FlutterSecureStorage>(
    () => const FlutterSecureStorage(),
  );

  getIt.registerLazySingleton<ApiClient>(
    () => ApiClient(getIt<FlutterSecureStorage>()),
  );

  getIt.registerLazySingleton<AppDatabase>(
    () => AppDatabase(),
  );

  // Services
  getIt.registerLazySingleton<LocationService>(
    () => LocationService(),
  );

  getIt.registerLazySingleton<CameraService>(
    () => CameraService(),
  );

  getIt.registerLazySingleton<PhotoValidator>(
    () => PhotoValidator(),
  );

  getIt.registerLazySingleton<SyncManager>(
    () => SyncManager(
      getIt<AppDatabase>(),
      getIt<ApiClient>(),
    ),
  );

  // Repositories
  getIt.registerLazySingleton<AuthRepository>(
    () => AuthRepository(
      getIt<ApiClient>(),
      getIt<FlutterSecureStorage>(),
    ),
  );

  getIt.registerLazySingleton<ActividadesRepository>(
    () => ActividadesRepository(
      getIt<ApiClient>(),
      getIt<AppDatabase>(),
    ),
  );

  getIt.registerLazySingleton<CapturaRepository>(
    () => CapturaRepository(
      getIt<ApiClient>(),
      getIt<AppDatabase>(),
      getIt<LocationService>(),
    ),
  );

  getIt.registerLazySingleton<SyncRepository>(
    () => SyncRepository(
      getIt<AppDatabase>(),
      getIt<SyncManager>(),
    ),
  );

  // Blocs
  getIt.registerFactory<AuthBloc>(
    () => AuthBloc(getIt<AuthRepository>()),
  );

  getIt.registerFactory<ActividadesBloc>(
    () => ActividadesBloc(getIt<ActividadesRepository>()),
  );

  getIt.registerFactory<CapturaBloc>(
    () => CapturaBloc(
      getIt<CapturaRepository>(),
      getIt<LocationService>(),
      getIt<PhotoValidator>(),
    ),
  );

  getIt.registerFactory<SyncBloc>(
    () => SyncBloc(getIt<SyncRepository>()),
  );
}
