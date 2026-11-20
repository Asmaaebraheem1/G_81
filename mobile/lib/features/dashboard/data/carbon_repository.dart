import 'dart:typed_data';

import '../../../core/database/app_database.dart';
import '../../../core/models.dart';
import '../../../core/network/api_client.dart';

/// A thin, typed gateway over `/api/v1`.
///
/// Server-calculated values are never recomputed here; this layer only
/// transports and caches them.
class CarbonRepository {
  CarbonRepository(this._api, {LocalCache? cache}) : _cache = cache;

  final ApiClient _api;
  final LocalCache? _cache;

  Future<List<Category>> categories({bool force = false}) async {
    const bucket = 'categories';
    if (!force) {
      final cached = await _safeBucket(bucket);
      if (cached.isNotEmpty) return cached.map(Category.fromJson).toList();
    }
    try {
      final data = maps(await _api.getData('/categories'));
      await _safePutMany(bucket, {
        for (final item in data) s(item['id']): item,
      });
      return data.map(Category.fromJson).toList();
    } catch (_) {
      final cached = await _safeBucket(bucket);
      if (cached.isNotEmpty) return cached.map(Category.fromJson).toList();
      rethrow;
    }
  }

  Future<List<Factor>> factors({int? categoryId, bool force = false}) async {
    final bucket = 'factors-${categoryId ?? 'all'}';
    if (!force) {
      final cached = await _safeBucket(bucket);
      if (cached.isNotEmpty) return cached.map(Factor.fromJson).toList();
    }
    try {
      final data = maps(
        await _api.getData(
          '/factors',
          query: {
            if (categoryId != null) 'category_id': categoryId,
          },
        ),
      );
      await _safePutMany(bucket, {
        for (final item in data) s(item['id']): item,
      });
      return data.map(Factor.fromJson).toList();
    } catch (_) {
      final cached = await _safeBucket(bucket);
      if (cached.isNotEmpty) return cached.map(Factor.fromJson).toList();
      rethrow;
    }
  }

  Future<Map<String, dynamic>> dashboard({
    String period = 'month',
    String? from,
    String? to,
  }) async {
    final key = 'dashboard-$period-${from ?? ''}-${to ?? ''}';
    try {
      final data = map(
        await _api.getData(
          '/dashboard/summary',
          query: {
            'period': period,
            if (from != null) 'from': from,
            if (to != null) 'to': to,
          },
        ),
      );
      await _safePut('dashboard', key, data);
      return data;
    } catch (_) {
      final cached = await _safeRead('dashboard', key);
      if (cached is Map) return map(cached);
      rethrow;
    }
  }

  Future<({List<ActivityRecord> items, Map<String, dynamic> meta})> records({
    int? categoryId,
    String? from,
    String? to,
    int page = 1,
    int perPage = 20,
  }) async {
    final body = await _api.getPage(
      '/records',
      query: {
        'page': page,
        'per_page': perPage,
        if (categoryId != null) 'category_id': categoryId,
        if (from != null) 'from': from,
        if (to != null) 'to': to,
        'sort': '-activity_date',
      },
    );
    final items = maps(body['data']).map(ActivityRecord.fromJson).toList();
    final meta = map(body['meta']);
    if (page == 1 && categoryId == null && from == null && to == null) {
      await _safePutMany('records', {
        for (final item in maps(body['data'])) s(item['id']): item,
      });
    }
    return (items: items, meta: meta);
  }

  Future<ActivityRecord> record(int id) async {
    try {
      return ActivityRecord.fromJson(map(await _api.getData('/records/$id')));
    } catch (_) {
      final cached = await _safeRead('records', '$id');
      if (cached is Map) return ActivityRecord.fromJson(map(cached));
      rethrow;
    }
  }

  Future<ActivityRecord> createRecord(Map<String, dynamic> body) async =>
      ActivityRecord.fromJson(map(await _api.postData('/records', body: body)));

  Future<ActivityRecord> updateRecord(
    int id,
    Map<String, dynamic> body,
  ) async =>
      ActivityRecord.fromJson(
        map(await _api.patchData('/records/$id', body: body)),
      );

  Future<void> deleteRecord(int id) async {
    await _api.deleteData('/records/$id');
  }

  Future<Map<String, dynamic>> reportSummary({
    String period = 'month',
    String? from,
    String? to,
  }) async =>
      map(await _api.getData(
        '/reports/summary',
        query: {
          'period': period,
          if (from != null) 'from': from,
          if (to != null) 'to': to,
        },
      ));

  Future<List<Map<String, dynamic>>> trend({int months = 6}) async {
    final data = map(
      await _api.getData('/reports/trend', query: {'months': months}),
    );
    return maps(data['points']);
  }

  Future<Map<String, dynamic>> categoryReport({String period = 'month'}) async =>
      map(await _api.getData(
        '/reports/categories',
        query: {'period': period},
      ));

  Future<List<Map<String, dynamic>>> topActivities({
    String period = 'month',
    int limit = 5,
  }) async {
    final data = map(
      await _api.getData(
        '/reports/top-activities',
        query: {'period': period, 'limit': limit},
      ),
    );
    return maps(data['activities']);
  }

  Future<Map<String, dynamic>> comparison({String period = 'month'}) async =>
      map(await _api.getData(
        '/reports/comparison',
        query: {'period': period},
      ));

  Future<Uint8List> exportCsv({
    required String from,
    required String to,
  }) =>
      _api.download('/reports/export.csv', query: {'from': from, 'to': to});

  Future<List<Goal>> goals({String? status}) async => maps(
        await _api.getData(
          '/goals',
          query: {if (status != null) 'status': status},
        ),
      ).map(Goal.fromJson).toList();

  Future<Goal> goal(int id) async =>
      Goal.fromJson(map(await _api.getData('/goals/$id')));

  Future<Goal> createGoal(Map<String, dynamic> body) async =>
      Goal.fromJson(map(await _api.postData('/goals', body: body)));

  Future<void> cancelGoal(int id) async {
    await _api.deleteData('/goals/$id');
  }

  Future<List<ReductionPlan>> plans() async => maps(
        await _api.getData('/plans'),
      ).map(ReductionPlan.fromJson).toList();

  Future<ReductionPlan> plan(int id) async =>
      ReductionPlan.fromJson(map(await _api.getData('/plans/$id')));

  Future<ReductionPlan> generatePlan({
    String period = 'month',
    String locale = 'en',
    int? goalId,
  }) async =>
      ReductionPlan.fromJson(
        map(
          await _api.postData(
            '/plans/generate',
            body: {
              'period': period,
              'locale': locale,
              if (goalId != null) 'goal_id': goalId,
            },
          ),
        ),
      );

  Future<PlanAction> updatePlanAction(
    int planId,
    int actionId,
    String status,
  ) async =>
      PlanAction.fromJson(
        map(
          await _api.patchData(
            '/plans/$planId/actions/$actionId',
            body: {'status': status},
          ),
        ),
      );

  Future<Map<String, dynamic>> planProgress(int id) async =>
      map(await _api.getData('/plans/$id/progress'));

  Future<List<Challenge>> challenges({String? status}) async => maps(
        await _api.getData(
          '/challenges',
          query: {if (status != null) 'status': status},
        ),
      ).map(Challenge.fromJson).toList();

  Future<Challenge> challenge(int id) async =>
      Challenge.fromJson(map(await _api.getData('/challenges/$id')));

  Future<Map<String, dynamic>> challengeDetail(int id) async =>
      map(await _api.getData('/challenges/$id'));

  Future<Map<String, dynamic>> challengeProgress(int id) async =>
      map(await _api.getData('/challenges/$id/progress'));

  Future<void> joinChallenge(int id) async {
    await _api.postData('/challenges/$id/join');
  }

  Future<Map<String, dynamic>> reportChallengeProgress(
    int id, {
    double? value,
  }) async =>
      map(
        await _api.postData(
          '/challenges/$id/progress',
          body: {if (value != null) 'value': value},
        ),
      );

  Future<Map<String, dynamic>> achievements() async =>
      map(await _api.getData('/achievements'));

  Future<Map<String, dynamic>> leaderboard({String period = 'month'}) async =>
      map(await _api.getData(
        '/leaderboard',
        query: {'period': period},
      ));

  Future<Map<String, dynamic>> notifications({bool unreadOnly = false}) async =>
      map(await _api.getData(
        '/notifications',
        query: {if (unreadOnly) 'unread': 1},
      ));

  Future<void> markNotificationRead(int id) async {
    await _api.patchData('/notifications/$id/read');
  }

  Future<void> markAllNotificationsRead() async {
    await _api.postData('/notifications/read-all');
  }

  Future<Map<String, dynamic>> notificationPreferences() async =>
      map(await _api.getData('/notification-preferences'));

  Future<Map<String, dynamic>> updateNotificationPreferences(
    Map<String, dynamic> body,
  ) async =>
      map(await _api.patchData('/notification-preferences', body: body));

  Future<Map<String, dynamic>> recommendedAlternatives({
    String locale = 'en',
  }) async =>
      map(await _api.getData(
        '/alternatives/recommended',
        query: {'locale': locale},
      ));

  Future<List<Map<String, dynamic>>> savedAlternatives() async => maps(
        await _api.getData('/alternatives/saved'),
      );

  Future<void> saveAlternative(int id, String status) async {
    await _api.postData(
      '/alternatives/$id/save',
      body: {'status': status},
    );
  }

  Future<List<Article>> articles() async => maps(
        await _api.getData('/content/articles'),
      ).map(Article.fromJson).toList();

  Future<Article> article(String slug) async =>
      Article.fromJson(map(await _api.getData('/content/articles/$slug')));

  Future<Map<String, dynamic>> aiStatus() async =>
      map(await _api.getData('/ai/status'));

  Future<Map<String, dynamic>> aiInsights({
    String period = 'month',
    String locale = 'en',
  }) async =>
      map(
        await _api.postData(
          '/ai/insights',
          body: {'period': period, 'locale': locale},
        ),
      );

  Future<Map<String, dynamic>> aiSummary({
    String period = 'month',
    String locale = 'en',
  }) async =>
      map(
        await _api.postData(
          '/ai/summary',
          body: {'period': period, 'locale': locale},
        ),
      );

  Future<Map<String, dynamic>> aiChat({
    required String message,
    int? conversationId,
    String locale = 'en',
  }) async =>
      map(
        await _api.postData(
          '/ai/chat',
          body: {
            'message': message,
            'locale': locale,
            if (conversationId != null) 'conversation_id': conversationId,
          },
        ),
      );

  Future<List<Map<String, dynamic>>> aiConversations() async => maps(
        await _api.getData('/ai/conversations'),
      );

  Future<Map<String, dynamic>> aiConversation(int id) async =>
      map(await _api.getData('/ai/conversations/$id'));

  Future<void> deleteConversation(int id) async {
    await _api.deleteData('/ai/conversations/$id');
  }

  Future<List<Map<String, dynamic>>> documents() async => maps(
        await _api.getData('/documents'),
      );

  Future<Map<String, dynamic>> uploadDocument({
    required Uint8List bytes,
    required String filename,
    required bool consent,
  }) async =>
      map(
        await _api.upload(
          '/documents',
          bytes: bytes,
          filename: filename,
          fields: {'consent': consent ? 'true' : 'false'},
        ),
      );

  Future<Map<String, dynamic>> extractDocument(int id) async =>
      map(await _api.postData('/documents/$id/extract'));

  Future<Map<String, dynamic>> confirmDocument(
    int id, {
    required int categoryId,
    required int factorId,
    required double quantity,
    required String unit,
    required String activityDate,
    String? vendor,
  }) async =>
      map(
        await _api.postData(
          '/documents/$id/confirm',
          body: {
            'category_id': categoryId,
            'factor_id': factorId,
            'quantity': quantity,
            'unit': unit,
            'activity_date': activityDate,
            if (vendor != null && vendor.isNotEmpty) 'vendor': vendor,
          },
        ),
      );

  Future<void> deleteDocument(int id) async {
    await _api.deleteData('/documents/$id');
  }

  Future<Map<String, dynamic>> organization() async =>
      map(await _api.getData('/organization'));

  Future<Map<String, dynamic>> profile() async =>
      map(await _api.getData('/profile'));

  Future<Map<String, dynamic>> updateProfile(Map<String, dynamic> body) async =>
      map(await _api.patchData('/profile', body: body));

  Future<Map<String, dynamic>> updateMe(Map<String, dynamic> body) async =>
      map(await _api.patchData('/auth/me', body: body));

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

  Future<Map<String, dynamic>> updateOrganization(
    Map<String, dynamic> body,
  ) async =>
      map(await _api.patchData('/organization', body: body));

  Future<dynamic> _safeRead(String bucket, String key) async {
    try {
      return await _cache?.read(bucket, key);
    } catch (_) {
      return null;
    }
  }

  Future<List<Map<String, dynamic>>> _safeBucket(String bucket) async {
    try {
      final rows = await _cache?.readBucket(bucket);
      if (rows is List) return maps(rows);
      return const [];
    } catch (_) {
      return const [];
    }
  }

  Future<void> _safePut(String bucket, String key, Object? value) async {
    try {
      await _cache?.put(bucket, key, value);
    } catch (_) {
      // Cache failures must never block API reads.
    }
  }

  Future<void> _safePutMany(
    String bucket,
    Map<String, Object?> values,
  ) async {
    try {
      await _cache?.putMany(bucket, values);
    } catch (_) {
      // Cache failures must never block API reads.
    }
  }
}
