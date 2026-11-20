import 'package:carbonwise/core/async_cubit.dart';
import 'package:carbonwise/core/format.dart';
import 'package:carbonwise/core/localization/app_localizations.dart';
import 'package:carbonwise/core/models.dart';
import 'package:carbonwise/core/network/api_exception.dart';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:intl/date_symbol_data_local.dart';

void main() {
  setUpAll(() async {
    await initializeDateFormatting('en');
    await initializeDateFormatting('ar');
  });
  group('dynamic helpers', () {
    test('n/ni/s tolerate strings, null and invalid values', () {
      expect(n(12), 12.0);
      expect(n('12.5'), 12.5);
      expect(n('bad', 3), 3);
      expect(n(null), 0);
      expect(ni(4.8), 4);
      expect(ni('7'), 7);
      expect(ni('bad', 2), 2);
      expect(s(null), '');
      expect(s(null, 'fallback'), 'fallback');
      expect(s(42), '42');
    });

    test('map/maps normalize untyped collections', () {
      expect(map({'a': 1}), {'a': 1});
      expect(map(<dynamic, dynamic>{'b': 2}), {'b': 2});
      expect(map('nope'), isEmpty);
      expect(maps([{'a': 1}, 'x']), [
        {'a': 1},
        <String, dynamic>{},
      ]);
      expect(maps(null), isEmpty);
    });
  });

  group('models', () {
    test('SessionUser parses defaults and org flags', () {
      final user = SessionUser.fromJson({
        'id': '3',
        'email': 'org@example.com',
        'full_name': 'Org Owner',
        'account_type': 'organization',
        'organization_id': '9',
        'is_org_owner': true,
        'is_verified': true,
      });
      expect(user.id, 3);
      expect(user.isOrganization, isTrue);
      expect(user.organizationId, 9);
      expect(user.locale, 'ar');
      expect(user.isVerified, isTrue);
    });

    test('Category, Factor and ActivityRecord parse nested values', () {
      final category = Category.fromJson({
        'id': 1,
        'key': 'electricity',
        'name_en': 'Electricity',
        'name_ar': 'الكهرباء',
        'icon': 'bolt',
        'color_hex': '#F5B300',
        'unit_hint': 'kWh',
      });
      expect(category.name('ar'), 'الكهرباء');
      expect(category.name('en'), 'Electricity');

      final factor = Factor.fromJson({
        'id': 2,
        'category_id': 1,
        'key': 'grid',
        'name_en': 'Grid',
        'name_ar': 'الشبكة',
        'unit': 'kWh',
        'factor_grams_co2e': 233,
        'source_name': 'EPA',
        'source_year': 2025,
        'region': 'UAE',
      });
      expect(factor.sourceLabel, 'EPA (2025) · UAE');
      expect(factor.name('ar'), 'الشبكة');

      final record = ActivityRecord.fromJson({
        'id': 4,
        'activity_date': '2026-06-18',
        'quantity': '100',
        'unit': 'kWh',
        'emissions_grams': 23300,
        'emissions_kg': 23.3,
        'formula': '100 kWh × 233 = 23,300 g',
        'factor_grams_co2e_snapshot': 233,
        'factor_source_snapshot': 'EPA',
        'notes': 'June bill',
        'status': 'active',
        'source': 'manual',
        'category': {
          'id': 1,
          'key': 'electricity',
          'name_en': 'Electricity',
          'name_ar': 'الكهرباء',
        },
        'factor': {
          'id': 2,
          'category_id': 1,
          'key': 'grid',
          'name_en': 'Grid',
          'name_ar': 'الشبكة',
          'unit': 'kWh',
          'factor_grams_co2e': 233,
        },
      });
      expect(record.emissionsKg, 23.3);
      expect(record.category?.name('ar'), 'الكهرباء');
      expect(record.factor?.unit, 'kWh');
      expect(record.activityDate, DateTime(2026, 6, 18));
      expect(record.source, 'manual');
    });

    test('ActivityRecord tolerates absent nested objects', () {
      final record = ActivityRecord.fromJson({'id': 1});
      expect(record.category, isNull);
      expect(record.factor, isNull);
      expect(record.status, 'active');
      expect(record.source, 'manual');
    });

    test('Goal parses progress and dates', () {
      final goal = Goal.fromJson({
        'id': 1,
        'title': 'Cut June',
        'target_percent': 10,
        'start_date': '2026-06-01',
        'end_date': '2026-06-30',
        'baseline_emissions_kg': 132.1,
        'target_emissions_kg': 118.9,
        'current_emissions_kg': 124.1,
        'achieved_percent': 57.5,
        'days_left': 11,
        'status': 'active',
        'on_track': true,
      });
      expect(goal.targetPercent, 10);
      expect(goal.onTrack, isTrue);
      expect(goal.daysLeft, 11);
      expect(goal.startDate, DateTime(2026, 6, 1));
    });

    test('ReductionPlan and PlanAction parse nested actions', () {
      final plan = ReductionPlan.fromJson({
        'id': 1,
        'title': 'A lighter June',
        'summary': 'Summary',
        'status': 'active',
        'source': 'template',
        'locale': 'ar',
        'generated_at': '2026-06-01T10:00:00Z',
        'actions': [
          {
            'id': 8,
            'title': 'LED',
            'description': 'Swap lights',
            'priority': 'high',
            'timeframe': 'this_month',
            'status': 'done',
            'estimated_saving_grams': 34200,
            'saving_assumption': '10% of category',
            'category_id': 2,
          },
        ],
      });
      expect(plan.actions, hasLength(1));
      expect(plan.actions.single.estimatedSavingGrams, 34200);
      expect(plan.actions.single.categoryId, 2);
      expect(plan.generatedAt, isNotNull);
    });

    test('Challenge reads nested participation', () {
      final joined = Challenge.fromJson({
        'id': 1,
        'title_en': 'Five records',
        'title_ar': 'خمسة سجلات',
        'description_en': 'Record five activities',
        'description_ar': 'سجّل خمسة أنشطة',
        'type': 'weekly',
        'target_type': 'record_count',
        'target_value': 5,
        'progress_value': 2,
        'points': 60,
        'challenge_status': 'active',
        'participation': {'status': 'joined'},
      });
      expect(joined.joined, isTrue);
      expect(joined.title('ar'), 'خمسة سجلات');
      expect(joined.participantStatus, 'joined');

      final open = Challenge.fromJson({'id': 2});
      expect(open.joined, isFalse);
      expect(open.participantStatus, 'not_joined');
      expect(open.status, 'active');
    });

    test('AppNotification and Article support bilingual content', () {
      final notification = AppNotification.fromJson({
        'id': 1,
        'type': 'goal',
        'title_en': 'Goal ready',
        'title_ar': 'الهدف جاهز',
        'body_en': 'Body',
        'body_ar': 'النص',
        'is_read': true,
        'created_at': '2026-06-18T10:16:00Z',
        'action_url': '/goals',
      });
      expect(notification.isRead, isTrue);
      expect(notification.title('ar'), 'الهدف جاهز');

      final article = Article.fromJson({
        'slug': 'how-to-start',
        'title_en': 'How to start',
        'title_ar': 'كيف تبدأ',
        'summary_en': 'Summary',
        'summary_ar': 'ملخص',
        'body_en': 'Body',
        'body_ar': 'نص',
        'category': 'basics',
        'image_path': '/static/guide.png',
      });
      expect(article.title('ar'), 'كيف تبدأ');
      expect(article.summary('en'), 'Summary');
      expect(article.body('ar'), 'نص');
    });

    test('Alternative supports saved status and assumptions', () {
      final alternative = Alternative.fromJson({
        'id': 1,
        'key': 'led',
        'title_en': 'LED switch',
        'title_ar': 'التحول إلى LED',
        'description_en': 'Description',
        'description_ar': 'الوصف',
        'assumption_en': '8% assumption',
        'assumption_ar': 'افتراض 8%',
        'estimated_reduction_percent': 8,
        'source_name': 'CarbonWise curated assumption',
        'recommended': true,
        'saved_status': 'saved',
      });
      expect(alternative.title('ar'), 'التحول إلى LED');
      expect(alternative.assumption('ar'), 'افتراض 8%');
      expect(alternative.recommended, isTrue);
      expect(alternative.savedStatus, 'saved');
    });
  });

  group('formatting', () {
    test('formatKg chooses sensible precision', () {
      expect(formatKg(0.5), '0.50');
      expect(formatKg(12.34), '12.3');
      expect(formatKg(1234.5), '1,235');
    });

    test('formatNumber and percent respect decimals', () {
      expect(formatNumber(1234.567), '1,234.57');
      expect(formatNumber(12, decimals: 2), '12.00');
      expect(formatPercent(15.44), '15.4%');
    });

    test('dates and greeting keys handle null and day parts', () {
      expect(parseApiDate('2026-06-18T10:00:00Z'), isNotNull);
      expect(parseApiDate('bad'), isNull);
      expect(formatDate(null), '—');
      expect(formatDateTime(null), '—');
      expect(formatDate(DateTime(2026, 6, 18)), contains('2026'));
      expect(greetingKeyFor(DateTime(2026, 6, 18, 8)), 'greetingMorning');
      expect(greetingKeyFor(DateTime(2026, 6, 18, 13)), 'greetingAfternoon');
      expect(greetingKeyFor(DateTime(2026, 6, 18, 20)), 'greetingEvening');
    });
  });

  group('AsyncCubit', () {
    test('runs a task, publishes data and supports silent refresh', () async {
      final cubit = AsyncCubit<int>(const AsyncState());
      await cubit.run(() async => 7);
      expect(cubit.state.status, AsyncStatus.ready);
      expect(cubit.state.data, 7);
      expect(cubit.state.hasData, isTrue);

      await cubit.run(() async => 9, silent: true, keepData: true);
      expect(cubit.state.data, 9);

      await cubit.run(() async => throw StateError('boom'), keepData: true);
      expect(cubit.state.status, AsyncStatus.error);
      expect(cubit.state.data, 9);
      expect(cubit.state.error, contains('boom'));
      expect(cubit.state.isLoading, isFalse);
      await cubit.close();
    });

    test('copyWith clears errors and can replace data', () {
      const state = AsyncState<int>(
        status: AsyncStatus.error,
        data: 1,
        error: 'bad',
        fromCache: true,
      );
      expect(state.copyWith(clearError: true).error, isNull);
      expect(state.copyWith(status: AsyncStatus.loading).isLoading, isTrue);
      expect(state.copyWith(data: 2).data, 2);
      expect(state.props, contains(true));
    });
  });

  group('ApiException', () {
    final request = RequestOptions(path: '/records');

    test('maps timeouts and network failures', () {
      final timeout = ApiException.fromDio(
        DioException(
          requestOptions: request,
          type: DioExceptionType.connectionTimeout,
        ),
      );
      expect(timeout.code, 'timeout');

      final offline = ApiException.fromDio(
        DioException(requestOptions: request, type: DioExceptionType.badResponse),
      );
      expect(offline.code, 'network_error');
    });

    test('maps structured API errors and flags', () {
      final error = ApiException.fromDio(
        DioException(
          requestOptions: request,
          response: Response(
            requestOptions: request,
            statusCode: 401,
            data: {
              'error': {
                'code': 'ai_disabled',
                'message': 'AI is off',
                'details': {'field': 'key'},
              },
            },
          ),
        ),
      );
      expect(error.code, 'ai_disabled');
      expect(error.isAiDisabled, isTrue);
      expect(error.isUnauthorized, isTrue);
      expect(error.details['field'], 'key');
      expect(error.toString(), contains('ai_disabled'));
    });

    test('maps plain server errors', () {
      final error = ApiException.fromDio(
        DioException(
          requestOptions: request,
          response: Response(
            requestOptions: request,
            statusCode: 500,
            statusMessage: 'Server exploded',
            data: 'not-json',
          ),
        ),
      );
      expect(error.code, 'server_error');
      expect(error.message, 'Server exploded');
      expect(error.isVisionUnavailable, isFalse);
    });
  });

  group('localization', () {
    test('every key is present in both languages', () {
      const en = AppLocalizations(Locale('en'));
      const ar = AppLocalizations(Locale('ar'));
      for (final key in const [
        'navHome',
        'navRecords',
        'assistant',
        'reports',
        'current',
        'bestEffort',
        'document',
        'week',
        'month',
        'year',
        'last30Days',
      ]) {
        expect(en.t(key), isNotEmpty);
        expect(ar.t(key), isNotEmpty);
        expect(en.t(key), isNot(key));
      }
    });

    test('delegate loads the requested language', () async {
      final delegate = AppLocalizations.delegate;
      final en = await delegate.load(const Locale('en'));
      final ar = await delegate.load(const Locale('ar'));
      expect(en.t('navHome'), 'Home');
      expect(ar.t('navHome'), 'الرئيسية');
      expect(ar.isArabic, isTrue);
      expect(delegate.shouldReload(delegate), isFalse);
    });
  });
}
