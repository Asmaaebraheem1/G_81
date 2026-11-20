import 'dart:async';
import 'dart:typed_data';

import 'package:dio/dio.dart';

import '../../core/config/app_config.dart';
import '../storage/token_store.dart';
import 'api_exception.dart';

/// The single HTTP entry point for the app.
///
/// Responsibilities: bearer injection, refresh-once, JSON envelopes,
/// multipart uploads, byte downloads, and error normalization.
class ApiClient {
  ApiClient({
    required TokenStore tokenStore,
    Dio? dio,
    String? baseUrl,
    this.onSessionExpired,
  })  : _tokens = tokenStore,
        _dio = dio ?? Dio() {
    _dio.options
      ..baseUrl = baseUrl ?? AppConfig.apiBaseUrl
      ..connectTimeout = const Duration(seconds: 10)
      ..receiveTimeout = const Duration(seconds: 45)
      ..sendTimeout = const Duration(seconds: 45)
      ..contentType = Headers.jsonContentType
      ..responseType = ResponseType.json;
    _dio.interceptors.add(
      InterceptorsWrapper(onRequest: _onRequest, onError: _onError),
    );
  }

  final Dio _dio;
  final TokenStore _tokens;
  void Function()? onSessionExpired;

  Future<bool>? _refreshing;
  bool _sessionExpired = false;

  Dio get raw => _dio;

  Future<void> _onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final isAuthCall = options.path.contains('/auth/login') ||
        options.path.contains('/auth/register') ||
        options.path.contains('/auth/refresh');
    if (!isAuthCall && options.headers['Authorization'] == null) {
      final access = await _tokens.readAccessToken();
      if (access != null && access.isNotEmpty) {
        options.headers['Authorization'] = 'Bearer $access';
      }
    }
    handler.next(options);
  }

  Future<void> _onError(
    DioException error,
    ErrorInterceptorHandler handler,
  ) async {
    final request = error.requestOptions;
    final isAuthCall = request.path.contains('/auth/login') ||
        request.path.contains('/auth/register') ||
        request.path.contains('/auth/refresh');
    final alreadyRetried = request.extra['carbonwise_retried'] == true;
    if (error.response?.statusCode != 401 || isAuthCall || alreadyRetried) {
      handler.next(error);
      return;
    }

    final refreshed = await _refreshOnce();
    final access = await _tokens.readAccessToken();
    if (!refreshed || access == null) {
      handler.next(error);
      return;
    }
    final options = request.copyWith(
      headers: {
        ...request.headers,
        'Authorization': 'Bearer $access',
      },
      extra: {...request.extra, 'carbonwise_retried': true},
    );
    try {
      final response = await _dio.fetch<dynamic>(options);
      handler.resolve(response);
    } on DioException catch (retryError) {
      handler.next(retryError);
    }
  }

  Future<bool> _refreshOnce() {
    final active = _refreshing;
    if (active != null) return active;
    final future = _performRefresh().whenComplete(() {
      _refreshing = null;
    });
    _refreshing = future;
    return future;
  }

  Future<bool> _performRefresh() async {
    final refresh = await _tokens.readRefreshToken();
    if (refresh == null || refresh.isEmpty) {
      await _expireSession();
      return false;
    }
    final refreshClient = Dio(
      BaseOptions(
        baseUrl: _dio.options.baseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 20),
        headers: {'Authorization': 'Bearer $refresh'},
      ),
    );
    try {
      final response = await refreshClient.post<dynamic>('/auth/refresh');
      final body = response.data;
      final data = body is Map<String, dynamic> ? body['data'] : null;
      if (data is! Map || data['access_token'] == null ||
          data['refresh_token'] == null) {
        await _expireSession();
        return false;
      }
      await _tokens.saveTokens(
        accessToken: data['access_token'].toString(),
        refreshToken: data['refresh_token'].toString(),
      );
      _sessionExpired = false;
      return true;
    } on DioException {
      await _expireSession();
      return false;
    }
  }

  Future<void> _expireSession() async {
    if (_sessionExpired) return;
    _sessionExpired = true;
    await _tokens.clear();
    onSessionExpired?.call();
  }

  Future<dynamic> getData(
    String path, {
    Map<String, dynamic>? query,
  }) async {
    try {
      final response = await _dio.get<dynamic>(path, queryParameters: query);
      return _unwrap(response.data);
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  Future<Map<String, dynamic>> getPage(
    String path, {
    Map<String, dynamic>? query,
  }) async {
    try {
      final response = await _dio.get<dynamic>(path, queryParameters: query);
      final body = response.data;
      if (body is Map<String, dynamic>) return body;
      return {'data': body, 'meta': const {}};
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  Future<dynamic> postData(String path, {Object? body}) async {
    try {
      final response = await _dio.post<dynamic>(path, data: body);
      return _unwrap(response.data);
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  Future<dynamic> patchData(String path, {Object? body}) async {
    try {
      final response = await _dio.patch<dynamic>(path, data: body);
      return _unwrap(response.data);
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  Future<dynamic> deleteData(String path, {Object? body}) async {
    try {
      final response = await _dio.delete<dynamic>(path, data: body);
      return _unwrap(response.data);
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  Future<dynamic> upload(
    String path, {
    required Uint8List bytes,
    required String filename,
    String field = 'file',
    Map<String, String> fields = const {},
  }) async {
    try {
      final form = FormData.fromMap({
        ...fields,
        field: MultipartFile.fromBytes(bytes, filename: filename),
      });
      final response = await _dio.post<dynamic>(path, data: form);
      return _unwrap(response.data);
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  Future<Uint8List> download(
    String path, {
    Map<String, dynamic>? query,
  }) async {
    try {
      final response = await _dio.get<List<int>>(
        path,
        queryParameters: query,
        options: Options(responseType: ResponseType.bytes),
      );
      return Uint8List.fromList(response.data ?? const []);
    } on DioException catch (error) {
      throw ApiException.fromDio(error);
    }
  }

  dynamic _unwrap(dynamic body) {
    if (body is Map<String, dynamic> && body.containsKey('data')) {
      return body['data'];
    }
    return body;
  }
}
