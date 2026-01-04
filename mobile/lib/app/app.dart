import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../features/auth/presentation/bloc/auth_bloc.dart';
import '../features/sync/presentation/bloc/sync_bloc.dart';
import '../core/di/injection.dart';
import 'routes.dart';
import 'theme.dart';

class TransMaintApp extends StatelessWidget {
  const TransMaintApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiBlocProvider(
      providers: [
        BlocProvider(create: (_) => getIt<AuthBloc>()..add(AuthCheckRequested())),
        BlocProvider(create: (_) => getIt<SyncBloc>()),
      ],
      child: MaterialApp.router(
        title: 'TransMaint',
        debugShowCheckedModeBanner: false,
        theme: AppTheme.lightTheme,
        darkTheme: AppTheme.darkTheme,
        themeMode: ThemeMode.system,
        routerConfig: appRouter,
      ),
    );
  }
}
