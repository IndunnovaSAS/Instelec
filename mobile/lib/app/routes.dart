import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

import '../features/auth/presentation/screens/login_screen.dart';
import '../features/auth/presentation/screens/splash_screen.dart';
import '../features/actividades/presentation/screens/actividades_screen.dart';
import '../features/actividades/presentation/screens/actividad_detalle_screen.dart';
import '../features/captura/presentation/screens/captura_screen.dart';
import '../features/captura/presentation/screens/camera_screen.dart';
import '../features/sync/presentation/screens/sync_screen.dart';
import '../features/asistencia/asistencia_screen.dart';
import '../shared/widgets/main_shell.dart';

final appRouter = GoRouter(
  initialLocation: '/splash',
  routes: [
    // Splash screen
    GoRoute(
      path: '/splash',
      builder: (context, state) => const SplashScreen(),
    ),

    // Login
    GoRoute(
      path: '/login',
      builder: (context, state) => const LoginScreen(),
    ),

    // Main shell with bottom navigation
    ShellRoute(
      builder: (context, state, child) => MainShell(child: child),
      routes: [
        // Home / Activities list
        GoRoute(
          path: '/',
          builder: (context, state) => const ActividadesScreen(),
          routes: [
            // Activity detail
            GoRoute(
              path: 'actividad/:id',
              builder: (context, state) => ActividadDetalleScreen(
                actividadId: state.pathParameters['id']!,
              ),
              routes: [
                // Field capture
                GoRoute(
                  path: 'captura',
                  builder: (context, state) => CapturaScreen(
                    actividadId: state.pathParameters['id']!,
                  ),
                ),
                // Camera for evidence
                GoRoute(
                  path: 'camera/:tipo',
                  builder: (context, state) => CameraScreen(
                    actividadId: state.pathParameters['id']!,
                    tipoEvidencia: state.pathParameters['tipo']!,
                  ),
                ),
              ],
            ),
          ],
        ),

        // Sync status
        GoRoute(
          path: '/sync',
          builder: (context, state) => const SyncScreen(),
        ),

        // Profile / Settings
        GoRoute(
          path: '/perfil',
          builder: (context, state) => const Scaffold(
            body: Center(child: Text('Perfil')),
          ),
        ),

        // Asistencia diaria
        GoRoute(
          path: '/asistencia',
          builder: (context, state) => const AsistenciaScreen(),
        ),
      ],
    ),
  ],
);
