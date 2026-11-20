import 'package:dio/dio.dart';

/// A normalized failure that widgets can render without touching Dio.
class ApiException implements Exception {
  const ApiException({
    required this.code,
    required this.message,
    this.statusCode,
    this.details = const {},
  });

  final String code;
  final String message;
  final int? statusCode;
  final Map<String, dynamic> details;

  bool get isAiDisabled => code == 'ai_disabled';
  bool get isVisionUnavailable => code == 'vision_unavailable';
  bool get isUnauthorized => statusCode == 401;

  static ApiException fromDio(DioException error) {
    final response = error.response;
    if (response == null) {
      if (error.type == DioExceptionType.connectionTimeout ||
          error.type == DioExceptionType.receiveTimeout ||
          error.type == DioExceptionType.sendTimeout) {
        return const ApiException(
          code: 'timeout',
          message: 'The request timed out. Please try again.',
        );
      }
      return const ApiException(
        code: 'network_error',
        message: 'No connection. Check your network and try again.',
      );
    }

    final body = response.data;
    if (body is Map && body['error'] is Map) {
      final errorBody = Map<String, dynamic>.from(body['error'] as Map);
      final rawDetails = errorBody['details'];
      return ApiException(
        code: (errorBody['code'] ?? 'server_error').toString(),
        message: (errorBody['message'] ?? 'Something went wrong.').toString(),
        statusCode: response.statusCode,
        details: rawDetails is Map
            ? Map<String, dynamic>.from(rawDetails)
            : <String, dynamic>{},
      );
    }
    return ApiException(
      code: 'server_error',
      message: response.statusMessage?.isNotEmpty == true
          ? response.statusMessage!
          : 'Something went wrong.',
      statusCode: response.statusCode,
    );
  }

  @override
  String toString() => 'ApiException($code, $statusCode): $message';
}
