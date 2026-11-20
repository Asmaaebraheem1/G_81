import 'package:carbonwise/core/localization/app_localizations.dart';
import 'package:carbonwise/core/models.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('localization exposes English and Arabic copy', () {
    const en = AppLocalizations(Locale('en'));
    const ar = AppLocalizations(Locale('ar'));

    expect(en.t('navHome'), 'Home');
    expect(ar.t('navHome'), 'الرئيسية');
    expect(ar.isArabic, isTrue);
  });

  test('API models parse backend-calculated emissions', () {
    final record = ActivityRecord.fromJson({
      'id': 7,
      'activity_date': '2026-06-01',
      'quantity': 100,
      'unit': 'kWh',
      'emissions_grams': 23300,
      'emissions_kg': 23.3,
      'formula': '100 kWh × 233 g CO2e/kWh = 23,300 g CO2e (23.30 kg)',
      'factor_grams_co2e_snapshot': 233,
      'factor_source_snapshot': 'Test source (2026)',
      'status': 'active',
      'source': 'manual',
      'category': {
        'id': 1,
        'key': 'electricity',
        'name_en': 'Electricity',
        'name_ar': 'الكهرباء',
        'icon': 'bolt',
        'color_hex': '#F5B300',
        'unit_hint': 'kWh',
      },
    });

    expect(record.emissionsGrams, 23300);
    expect(record.category?.name('ar'), 'الكهرباء');
    expect(record.formula, contains('23.30 kg'));
  });

  test('unknown localization keys fall back to the key', () {
    const en = AppLocalizations(Locale('en'));
    expect(en.t('missing.key'), 'missing.key');
  });
}
