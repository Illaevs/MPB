class AuthSession {
  const AuthSession({
    this.accessToken,
    this.refreshToken,
    this.user,
    this.permissions = const <String, dynamic>{},
    this.isSuperuser = false,
    this.isLoading = false,
    this.error,
  });

  final String? accessToken;
  final String? refreshToken;
  final Map<String, dynamic>? user;
  final Map<String, dynamic> permissions;
  final bool isSuperuser;
  final bool isLoading;
  final String? error;

  bool get isAuthenticated => accessToken != null && accessToken!.isNotEmpty && user != null;

  AuthSession copyWith({
    String? accessToken,
    String? refreshToken,
    Map<String, dynamic>? user,
    Map<String, dynamic>? permissions,
    bool? isSuperuser,
    bool? isLoading,
    String? error,
    bool clearError = false,
    bool clearSession = false,
  }) {
    if (clearSession) {
      return AuthSession(
        isLoading: isLoading ?? false,
        error: clearError ? null : error,
      );
    }
    return AuthSession(
      accessToken: accessToken ?? this.accessToken,
      refreshToken: refreshToken ?? this.refreshToken,
      user: user ?? this.user,
      permissions: permissions ?? this.permissions,
      isSuperuser: isSuperuser ?? this.isSuperuser,
      isLoading: isLoading ?? this.isLoading,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

