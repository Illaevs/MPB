import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import '../../core/auth/session_controller.dart';
import '../../features/auth/presentation/login_screen.dart';
import '../../features/home/presentation/home_screen.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final session = ref.watch(sessionControllerProvider);

  return GoRouter(
    initialLocation: '/home',
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/home',
        builder: (context, state) => const HomeScreen(),
      ),
    ],
    redirect: (context, state) {
      final isAuth = session.isAuthenticated;
      final isLoading = session.isLoading;
      final isLogin = state.matchedLocation == '/login';

      if (isLoading) {
        return null;
      }
      if (!isAuth) {
        return isLogin ? null : '/login';
      }
      if (isLogin) {
        return '/home';
      }
      return null;
    },
  );
});

