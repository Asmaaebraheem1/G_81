import 'package:shared_preferences/shared_preferences.dart';

class SettingsStore {
  SettingsStore(this._prefs);

  final SharedPreferences _prefs;
  static const _localeKey = 'carbonwise.locale';
  static const _onboardingKey = 'carbonwise.onboarding_seen';

  static Future<SettingsStore> load() async =>
      SettingsStore(await SharedPreferences.getInstance());

  String get localeCode => _prefs.getString(_localeKey) ?? 'ar';

  Future<void> setLocaleCode(String code) async {
    await _prefs.setString(_localeKey, code);
  }

  bool get onboardingSeen => _prefs.getBool(_onboardingKey) ?? false;

  Future<void> setOnboardingSeen() async {
    await _prefs.setBool(_onboardingKey, true);
  }
}
