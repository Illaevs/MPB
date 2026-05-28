import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/auth/session_controller.dart';
import 'router/app_router.dart';
import 'theme/app_theme.dart';

class EnterpriseMobileApp extends ConsumerStatefulWidget {
  const EnterpriseMobileApp({super.key});

  @override
  ConsumerState<EnterpriseMobileApp> createState() => _EnterpriseMobileAppState();
}

class _EnterpriseMobileAppState extends ConsumerState<EnterpriseMobileApp> {
  @override
  void initState() {
    super.initState();
    Future.microtask(() => ref.read(sessionControllerProvider.notifier).restore());
  }

  @override
  Widget build(BuildContext context) {
    final router = ref.watch(appRouterProvider);
    return MaterialApp.router(
      title: 'Enterprise система управления',
      debugShowCheckedModeBanner: false,
      theme: buildAppTheme(),
      routerConfig: router,
    );
  }
}
