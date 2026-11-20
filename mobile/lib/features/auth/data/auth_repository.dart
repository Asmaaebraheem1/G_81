import '../../../core/network/api_client.dart';
import '../../../core/storage/token_store.dart';
import '../../../core/models.dart';

class AuthRepository {
  AuthRepository(this._api, this._tokens);

  final ApiClient _api;
  final TokenStore _tokens;

  Future<SessionUser> login(String email, String password) async {
    final data = map(await _api.postData(
      '/auth/login',
      body: {'email': email.trim(), 'password': password},
    ));
    return _persistSession(data);
  }

  Future<SessionUser> register({
    required String fullName,
    required String email,
    required String password,
    required String accountType,
    required String locale,
    String? organizationName,
  }) async {
    final body = <String, dynamic>{
      'full_name': fullName.trim(),
      'email': email.trim(),
      'password': password,
      'account_type': accountType,
      'locale': locale,
      'timezone': 'UTC',
      if (accountType == 'organization')
        'organization_name': (organizationName ?? fullName).trim(),
    };
    final data = map(await _api.postData('/auth/register', body: body));
    return _persistSession(data);
  }

  Future<SessionUser> _persistSession(Map<String, dynamic> data) async {
    final access = s(data['access_token']);
    final refresh = s(data['refresh_token']);
    if (access.isEmpty || refresh.isEmpty) {
      throw StateError('The server did not return a token pair.');
    }
    await _tokens.saveTokens(accessToken: access, refreshToken: refresh);
    return SessionUser.fromJson(map(data['user']));
  }

  Future<SessionUser?> restoreSession() async {
    final refresh = await _tokens.readRefreshToken();
    if (refresh == null || refresh.isEmpty) return null;
    try {
      final data = await _api.getData('/auth/me');
      return SessionUser.fromJson(map(map(data)['user']));
    } catch (_) {
      await _tokens.clear();
      return null;
    }
  }

  Future<SessionUser> me() async {
    final data = await _api.getData('/auth/me');
    return SessionUser.fromJson(map(map(data)['user']));
  }

  Future<Map<String, dynamic>> profile() async =>
      map(await _api.getData('/profile'));

  Future<Map<String, dynamic>> updateProfile(Map<String, dynamic> body) async =>
      map(await _api.patchData('/profile', body: body));

  Future<SessionUser> updateMe(Map<String, dynamic> body) async {
    final data = await _api.patchData('/auth/me', body: body);
    return SessionUser.fromJson(map(data));
  }

  Future<void> changePassword({
    required String currentPassword,
    required String newPassword,
  }) async {
    await _api.patchData(
      '/auth/password',
      body: {
        'current_password': currentPassword,
        'new_password': newPassword,
      },
    );
  }

  Future<void> logout() async {
    final refresh = await _tokens.readRefreshToken();
    try {
      await _api.postData(
        '/auth/logout',
        body: {'all_devices': false, 'refresh_token': refresh},
      );
    } catch (_) {
      // A local sign-out must always succeed.
    } finally {
      await _tokens.clear();
    }
  }
}
