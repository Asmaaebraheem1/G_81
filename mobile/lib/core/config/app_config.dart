import 'package:flutter/foundation.dart';

/// Central runtime configuration.
///
/// Override the API with:
/// `flutter run --dart-define=API_BASE_URL=http://10.0.2.2:5000/api/v1`
class AppConfig {
  AppConfig._();

  static const String _override = String.fromEnvironment('API_BASE_URL');

  static String get apiBaseUrl {
    if (_override.isNotEmpty) return _override;
    if (kIsWeb) return 'http://127.0.0.1:5000/api/v1';
    return switch (defaultTargetPlatform) {
      TargetPlatform.android => 'http://10.0.2.2:5000/api/v1',
      _ => 'http://127.0.0.1:5000/api/v1',
    };
  }

  static const String appName = 'CarbonWise';
  static const String appNameAr = 'كربونوايز';
  static const String supportEmail = 'hello@carbonwise.demo';

  /// The deterministic demo timeline ends on this date.
  static final DateTime demoToday = DateTime(2026, 6, 30);
}
