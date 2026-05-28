import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../network/api_client.dart';

final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository(ref.watch(apiClientProvider));
});

class AuthRepository {
  AuthRepository(this._client);

  final ApiClient _client;

  Future<Map<String, dynamic>> login({
    required String email,
    required String password,
  }) {
    return _client.postJson(
      '/api/v1/auth/mobile/login',
      data: {
        'email': email,
        'password': password,
      },
    );
  }

  Future<Map<String, dynamic>> verifyTwoFactor({
    required String challengeToken,
    required String code,
  }) {
    return _client.postJson(
      '/api/v1/auth/mobile/verify-2fa',
      data: {
        'challenge_token': challengeToken,
        'code': code,
      },
    );
  }

  Future<Map<String, dynamic>> refresh(String refreshToken) {
    return _client.postJson(
      '/api/v1/auth/mobile/refresh',
      data: {
        'refresh_token': refreshToken,
      },
    );
  }
}

