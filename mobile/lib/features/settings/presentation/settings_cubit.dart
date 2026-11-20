import 'package:equatable/equatable.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/storage/settings_store.dart';

class SettingsState extends Equatable {
  const SettingsState({required this.locale});

  final Locale locale;

  bool get isArabic => locale.languageCode == 'ar';

  @override
  List<Object?> get props => [locale.languageCode];
}

class SettingsCubit extends Cubit<SettingsState> {
  SettingsCubit(this._store)
      : super(SettingsState(locale: Locale(_store.localeCode)));

  final SettingsStore _store;

  Future<void> setLanguage(String code) async {
    if (code != 'en' && code != 'ar') return;
    await _store.setLocaleCode(code);
    emit(SettingsState(locale: Locale(code)));
  }

  Future<void> toggleLanguage() async {
    await setLanguage(state.isArabic ? 'en' : 'ar');
  }

  Future<void> markOnboardingSeen() => _store.setOnboardingSeen();
}
