double n(dynamic value, [double fallback = 0]) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '') ?? fallback;
}

int ni(dynamic value, [int fallback = 0]) {
  if (value is num) return value.toInt();
  return int.tryParse(value?.toString() ?? '') ?? fallback;
}

String s(dynamic value, [String fallback = '']) {
  if (value == null) return fallback;
  return value.toString();
}

Map<String, dynamic> map(dynamic value) {
  if (value is Map<String, dynamic>) return value;
  if (value is Map) return Map<String, dynamic>.from(value);
  return <String, dynamic>{};
}

List<Map<String, dynamic>> maps(dynamic value) {
  if (value is List) return value.map(map).toList(growable: false);
  return const [];
}

class SessionUser {
  const SessionUser({
    required this.id,
    required this.email,
    required this.fullName,
    required this.accountType,
    required this.locale,
    required this.organizationId,
    required this.isOrgOwner,
    required this.isVerified,
  });

  final int id;
  final String email;
  final String fullName;
  final String accountType;
  final String locale;
  final int? organizationId;
  final bool isOrgOwner;
  final bool isVerified;

  bool get isOrganization => accountType == 'organization';

  factory SessionUser.fromJson(Map<String, dynamic> json) => SessionUser(
        id: ni(json['id']),
        email: s(json['email']),
        fullName: s(json['full_name']),
        accountType: s(json['account_type'], 'individual'),
        locale: s(json['locale'], 'ar'),
        organizationId: json['organization_id'] == null
            ? null
            : ni(json['organization_id']),
        isOrgOwner: json['is_org_owner'] == true,
        isVerified: json['is_verified'] == true,
      );
}

class Category {
  const Category({
    required this.id,
    required this.key,
    required this.nameEn,
    required this.nameAr,
    required this.icon,
    required this.colorHex,
    required this.unitHint,
  });

  final int id;
  final String key;
  final String nameEn;
  final String nameAr;
  final String icon;
  final String colorHex;
  final String unitHint;

  String name(String language) => language == 'ar' ? nameAr : nameEn;

  factory Category.fromJson(Map<String, dynamic> json) => Category(
        id: ni(json['id']),
        key: s(json['key']),
        nameEn: s(json['name_en']),
        nameAr: s(json['name_ar']),
        icon: s(json['icon']),
        colorHex: s(json['color_hex']),
        unitHint: s(json['unit_hint']),
      );
}

class Factor {
  const Factor({
    required this.id,
    required this.categoryId,
    required this.key,
    required this.nameEn,
    required this.nameAr,
    required this.unit,
    required this.factorGrams,
    required this.sourceName,
    required this.sourceYear,
    required this.region,
  });

  final int id;
  final int categoryId;
  final String key;
  final String nameEn;
  final String nameAr;
  final String unit;
  final int factorGrams;
  final String sourceName;
  final int? sourceYear;
  final String region;

  String name(String language) => language == 'ar' ? nameAr : nameEn;
  String get sourceLabel =>
      '$sourceName${sourceYear == null ? '' : ' ($sourceYear)'} · $region';

  factory Factor.fromJson(Map<String, dynamic> json) => Factor(
        id: ni(json['id']),
        categoryId: ni(json['category_id']),
        key: s(json['key']),
        nameEn: s(json['name_en']),
        nameAr: s(json['name_ar']),
        unit: s(json['unit']),
        factorGrams: ni(json['factor_grams_co2e']),
        sourceName: s(json['source_name']),
        sourceYear: json['source_year'] == null ? null : ni(json['source_year']),
        region: s(json['region'], 'GLOBAL'),
      );
}

class ActivityRecord {
  const ActivityRecord({
    required this.id,
    required this.activityDate,
    required this.quantity,
    required this.unit,
    required this.emissionsGrams,
    required this.emissionsKg,
    required this.formula,
    required this.factorGrams,
    required this.factorSource,
    required this.notes,
    required this.status,
    required this.source,
    required this.category,
    required this.factor,
  });

  final int id;
  final DateTime? activityDate;
  final double quantity;
  final String unit;
  final int emissionsGrams;
  final double emissionsKg;
  final String formula;
  final int factorGrams;
  final String factorSource;
  final String notes;
  final String status;
  final String source;
  final Category? category;
  final Factor? factor;

  factory ActivityRecord.fromJson(Map<String, dynamic> json) {
    final categoryJson = json['category'];
    final factorJson = json['factor'];
    return ActivityRecord(
      id: ni(json['id']),
      activityDate: DateTime.tryParse(s(json['activity_date'])),
      quantity: n(json['quantity']),
      unit: s(json['unit']),
      emissionsGrams: ni(json['emissions_grams']),
      emissionsKg: n(json['emissions_kg']),
      formula: s(json['formula']),
      factorGrams: ni(json['factor_grams_co2e_snapshot']),
      factorSource: s(json['factor_source_snapshot']),
      notes: s(json['notes']),
      status: s(json['status'], 'active'),
      source: s(json['source'], 'manual'),
      category: categoryJson is Map ? Category.fromJson(map(categoryJson)) : null,
      factor: factorJson is Map ? Factor.fromJson(map(factorJson)) : null,
    );
  }
}

class Goal {
  const Goal({
    required this.id,
    required this.title,
    required this.targetPercent,
    required this.startDate,
    required this.endDate,
    required this.baselineKg,
    required this.targetKg,
    required this.currentKg,
    required this.achievedPercent,
    required this.daysLeft,
    required this.status,
    required this.onTrack,
  });

  final int id;
  final String title;
  final double targetPercent;
  final DateTime? startDate;
  final DateTime? endDate;
  final double baselineKg;
  final double targetKg;
  final double currentKg;
  final double achievedPercent;
  final int daysLeft;
  final String status;
  final bool onTrack;

  factory Goal.fromJson(Map<String, dynamic> json) => Goal(
        id: ni(json['id']),
        title: s(json['title']),
        targetPercent: n(json['target_percent']),
        startDate: DateTime.tryParse(s(json['start_date'])),
        endDate: DateTime.tryParse(s(json['end_date'])),
        baselineKg: n(json['baseline_emissions_kg']),
        targetKg: n(json['target_emissions_kg']),
        currentKg: n(json['current_emissions_kg']),
        achievedPercent: n(json['achieved_percent']),
        daysLeft: ni(json['days_left']),
        status: s(json['status'], 'active'),
        onTrack: json['on_track'] == true,
      );
}

class PlanAction {
  const PlanAction({
    required this.id,
    required this.title,
    required this.description,
    required this.priority,
    required this.timeframe,
    required this.status,
    required this.estimatedSavingGrams,
    required this.savingAssumption,
    required this.categoryId,
  });

  final int id;
  final String title;
  final String description;
  final String priority;
  final String timeframe;
  final String status;
  final int estimatedSavingGrams;
  final String savingAssumption;
  final int? categoryId;

  factory PlanAction.fromJson(Map<String, dynamic> json) => PlanAction(
        id: ni(json['id']),
        title: s(json['title']),
        description: s(json['description']),
        priority: s(json['priority'], 'medium'),
        timeframe: s(json['timeframe'], 'this_month'),
        status: s(json['status'], 'pending'),
        estimatedSavingGrams: ni(json['estimated_saving_grams']),
        savingAssumption: s(json['saving_assumption']),
        categoryId: json['category_id'] == null ? null : ni(json['category_id']),
      );
}

class ReductionPlan {
  const ReductionPlan({
    required this.id,
    required this.title,
    required this.summary,
    required this.status,
    required this.source,
    required this.locale,
    required this.generatedAt,
    required this.actions,
  });

  final int id;
  final String title;
  final String summary;
  final String status;
  final String source;
  final String locale;
  final DateTime? generatedAt;
  final List<PlanAction> actions;

  factory ReductionPlan.fromJson(Map<String, dynamic> json) => ReductionPlan(
        id: ni(json['id']),
        title: s(json['title']),
        summary: s(json['summary']),
        status: s(json['status'], 'draft'),
        source: s(json['source'], 'template'),
        locale: s(json['locale'], 'en'),
        generatedAt: DateTime.tryParse(s(json['generated_at'])),
        actions: maps(json['actions']).map(PlanAction.fromJson).toList(),
      );
}

class Challenge {
  const Challenge({
    required this.id,
    required this.titleEn,
    required this.titleAr,
    required this.descriptionEn,
    required this.descriptionAr,
    required this.type,
    required this.targetType,
    required this.targetValue,
    required this.progressValue,
    required this.points,
    required this.startDate,
    required this.endDate,
    required this.status,
    required this.joined,
    required this.participantStatus,
  });

  final int id;
  final String titleEn;
  final String titleAr;
  final String descriptionEn;
  final String descriptionAr;
  final String type;
  final String targetType;
  final double targetValue;
  final double progressValue;
  final int points;
  final DateTime? startDate;
  final DateTime? endDate;
  final String status;
  final bool joined;
  final String participantStatus;

  String title(String language) => language == 'ar' ? titleAr : titleEn;
  String description(String language) =>
      language == 'ar' ? descriptionAr : descriptionEn;

  factory Challenge.fromJson(Map<String, dynamic> json) {
    final participation = json['participation'] is Map
        ? map(json['participation'])
        : null;
    return Challenge(
      id: ni(json['id']),
      titleEn: s(json['title_en']),
      titleAr: s(json['title_ar']),
      descriptionEn: s(json['description_en']),
      descriptionAr: s(json['description_ar']),
      type: s(json['type'], 'weekly'),
      targetType: s(json['target_type'], 'record_count'),
      targetValue: n(json['target_value']),
      progressValue: n(json['progress_value']),
      points: ni(json['points']),
      startDate: DateTime.tryParse(s(json['start_date'])),
      endDate: DateTime.tryParse(s(json['end_date'])),
      status: s(json['challenge_status'], 'active'),
      joined: participation != null,
      participantStatus: participation == null
          ? 'not_joined'
          : s(participation['status'], 'joined'),
    );
  }
}

class AppNotification {
  const AppNotification({
    required this.id,
    required this.type,
    required this.titleEn,
    required this.titleAr,
    required this.bodyEn,
    required this.bodyAr,
    required this.isRead,
    required this.createdAt,
    required this.actionUrl,
  });

  final int id;
  final String type;
  final String titleEn;
  final String titleAr;
  final String bodyEn;
  final String bodyAr;
  final bool isRead;
  final DateTime? createdAt;
  final String actionUrl;

  String title(String language) => language == 'ar' ? titleAr : titleEn;
  String body(String language) => language == 'ar' ? bodyAr : bodyEn;

  factory AppNotification.fromJson(Map<String, dynamic> json) =>
      AppNotification(
        id: ni(json['id']),
        type: s(json['type']),
        titleEn: s(json['title_en']),
        titleAr: s(json['title_ar']),
        bodyEn: s(json['body_en']),
        bodyAr: s(json['body_ar']),
        isRead: json['is_read'] == true,
        createdAt: DateTime.tryParse(s(json['created_at'])),
        actionUrl: s(json['action_url']),
      );
}

class Article {
  const Article({
    required this.slug,
    required this.titleEn,
    required this.titleAr,
    required this.summaryEn,
    required this.summaryAr,
    required this.bodyEn,
    required this.bodyAr,
    required this.category,
    required this.imagePath,
  });

  final String slug;
  final String titleEn;
  final String titleAr;
  final String summaryEn;
  final String summaryAr;
  final String bodyEn;
  final String bodyAr;
  final String category;
  final String imagePath;

  String title(String language) => language == 'ar' ? titleAr : titleEn;
  String summary(String language) => language == 'ar' ? summaryAr : summaryEn;
  String body(String language) => language == 'ar' ? bodyAr : bodyEn;

  factory Article.fromJson(Map<String, dynamic> json) => Article(
        slug: s(json['slug']),
        titleEn: s(json['title_en']),
        titleAr: s(json['title_ar']),
        summaryEn: s(json['summary_en']),
        summaryAr: s(json['summary_ar']),
        bodyEn: s(json['body_en']),
        bodyAr: s(json['body_ar']),
        category: s(json['category']),
        imagePath: s(json['image_path']),
      );
}

class Alternative {
  const Alternative({
    required this.id,
    required this.key,
    required this.titleEn,
    required this.titleAr,
    required this.descriptionEn,
    required this.descriptionAr,
    required this.assumptionEn,
    required this.assumptionAr,
    required this.estimatedReductionPercent,
    required this.sourceName,
    required this.source,
    required this.recommended,
    required this.savedStatus,
  });

  final int id;
  final String key;
  final String titleEn;
  final String titleAr;
  final String descriptionEn;
  final String descriptionAr;
  final String assumptionEn;
  final String assumptionAr;
  final double estimatedReductionPercent;
  final String sourceName;
  final String source;
  final bool recommended;
  final String? savedStatus;

  String title(String language) => language == 'ar' ? titleAr : titleEn;
  String description(String language) =>
      language == 'ar' ? descriptionAr : descriptionEn;
  String assumption(String language) =>
      language == 'ar' ? assumptionAr : assumptionEn;

  factory Alternative.fromJson(Map<String, dynamic> json) => Alternative(
        id: ni(json['id']),
        key: s(json['key']),
        titleEn: s(json['title_en']),
        titleAr: s(json['title_ar']),
        descriptionEn: s(json['description_en']),
        descriptionAr: s(json['description_ar']),
        assumptionEn: s(json['assumption_en']),
        assumptionAr: s(json['assumption_ar']),
        estimatedReductionPercent: n(json['estimated_reduction_percent']),
        sourceName: s(json['source_name']),
        source: s(json['source'], 'catalog'),
        recommended: json['recommended'] == true,
        savedStatus:
            json['saved_status'] == null ? null : s(json['saved_status']),
      );
}
