import 'dart:convert';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

final sessionStorageProvider = Provider<SessionStorage>((ref) {
  return const SessionStorage(FlutterSecureStorage());
});

class SessionStorage {
  const SessionStorage(this._storage);

  final FlutterSecureStorage _storage;

  static const _accessTokenKey = 'mobile_access_token';
  static const _refreshTokenKey = 'mobile_refresh_token';
  static const _userKey = 'mobile_user_json';
  static const _permissionsKey = 'mobile_permissions_json';
  static const _isSuperuserKey = 'mobile_is_superuser';

  Future<void> saveSession({
    required String accessToken,
    required String refreshToken,
    required Map<String, dynamic> user,
    required Map<String, dynamic> permissions,
    required bool isSuperuser,
  }) async {
    await _storage.write(key: _accessTokenKey, value: accessToken);
    await _storage.write(key: _refreshTokenKey, value: refreshToken);
    await _storage.write(key: _userKey, value: jsonEncode(user));
    await _storage.write(key: _permissionsKey, value: jsonEncode(permissions));
    await _storage.write(key: _isSuperuserKey, value: isSuperuser ? '1' : '0');
  }

  Future<Map<String, dynamic>?> loadSession() async {
    final accessToken = await _storage.read(key: _accessTokenKey);
    final refreshToken = await _storage.read(key: _refreshTokenKey);
    final userJson = await _storage.read(key: _userKey);
    final permissionsJson = await _storage.read(key: _permissionsKey);
    final isSuperuser = await _storage.read(key: _isSuperuserKey);

    if (accessToken == null || refreshToken == null || userJson == null) {
      return null;
    }
    return {
      'access_token': accessToken,
      'refresh_token': refreshToken,
      'user': jsonDecode(userJson),
      'permissions': permissionsJson == null ? <String, dynamic>{} : jsonDecode(permissionsJson),
      'is_superuser': isSuperuser == '1',
    };
  }

  Future<void> clear() async {
    await _storage.delete(key: _accessTokenKey);
    await _storage.delete(key: _refreshTokenKey);
    await _storage.delete(key: _userKey);
    await _storage.delete(key: _permissionsKey);
    await _storage.delete(key: _isSuperuserKey);
  }
}

