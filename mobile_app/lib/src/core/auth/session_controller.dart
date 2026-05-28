import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../network/api_client.dart';
import 'auth_repository.dart';
import 'auth_session.dart';
import 'session_storage.dart';

final sessionControllerProvider = StateNotifierProvider<SessionController, AuthSession>((ref) {
  return SessionController(
    ref.watch(authRepositoryProvider),
    ref.watch(sessionStorageProvider),
    ref.watch(apiClientProvider),
  );
});

class SessionController extends StateNotifier<AuthSession> {
  SessionController(this._authRepository, this._storage, this._apiClient)
      : super(const AuthSession(isLoading: true));

  final AuthRepository _authRepository;
  final SessionStorage _storage;
  final ApiClient _apiClient;

  String? _pendingChallengeToken;

  String? get pendingChallengeToken => _pendingChallengeToken;

  Future<void> restore() async {
    state = state.copyWith(isLoading: true, clearError: true);
    final saved = await _storage.loadSession();
    if (saved == null) {
      _apiClient.setBearerToken(null);
      state = const AuthSession(isLoading: false);
      return;
    }
    final accessToken = saved['access_token'] as String?;
    final refreshToken = saved['refresh_token'] as String?;
    final user = (saved['user'] as Map?)?.cast<String, dynamic>();
    final permissions = ((saved['permissions'] as Map?) ?? <String, dynamic>{}).cast<String, dynamic>();
    final isSuperuser = saved['is_superuser'] == true;

    if (accessToken == null || refreshToken == null || user == null) {
      await logout();
      return;
    }

    _apiClient.setBearerToken(accessToken);
    state = AuthSession(
      accessToken: accessToken,
      refreshToken: refreshToken,
      user: user,
      permissions: permissions,
      isSuperuser: isSuperuser,
      isLoading: false,
    );
  }

  Future<bool> login(String email, String password) async {
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final response = await _authRepository.login(email: email, password: password);
      final requires2fa = response['requires_2fa'] == true;
      if (requires2fa) {
        _pendingChallengeToken = response['challenge_token'] as String?;
        state = state.copyWith(
          isLoading: false,
          error: 'Требуется код 2FA',
          clearSession: true,
        );
        return false;
      }
      await _setAuthenticatedState(response);
      return true;
    } catch (error) {
      state = state.copyWith(
        isLoading: false,
        clearSession: true,
        error: error.toString(),
      );
      return false;
    }
  }

  Future<bool> verifyTwoFactor(String code) async {
    if (_pendingChallengeToken == null || _pendingChallengeToken!.isEmpty) {
      state = state.copyWith(isLoading: false, error: 'Не найден challenge token для 2FA.');
      return false;
    }
    state = state.copyWith(isLoading: true, clearError: true);
    try {
      final response = await _authRepository.verifyTwoFactor(
        challengeToken: _pendingChallengeToken!,
        code: code,
      );
      await _setAuthenticatedState(response);
      _pendingChallengeToken = null;
      return true;
    } catch (error) {
      state = state.copyWith(isLoading: false, error: error.toString());
      return false;
    }
  }

  Future<void> logout() async {
    _pendingChallengeToken = null;
    _apiClient.setBearerToken(null);
    await _storage.clear();
    state = const AuthSession(isLoading: false);
  }

  Future<void> _setAuthenticatedState(Map<String, dynamic> response) async {
    final accessToken = response['access_token'] as String?;
    final refreshToken = response['refresh_token'] as String?;
    final user = (response['user'] as Map?)?.cast<String, dynamic>();
    final permissions = ((response['permissions'] as Map?) ?? <String, dynamic>{}).cast<String, dynamic>();
    final isSuperuser = response['is_superuser'] == true;

    if (accessToken == null || refreshToken == null || user == null) {
      throw Exception('Backend не вернул access_token / refresh_token / user.');
    }

    _apiClient.setBearerToken(accessToken);
    await _storage.saveSession(
      accessToken: accessToken,
      refreshToken: refreshToken,
      user: user,
      permissions: permissions,
      isSuperuser: isSuperuser,
    );
    state = AuthSession(
      accessToken: accessToken,
      refreshToken: refreshToken,
      user: user,
      permissions: permissions,
      isSuperuser: isSuperuser,
      isLoading: false,
    );
  }
}
