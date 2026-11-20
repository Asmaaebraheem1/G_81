import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../core/async_cubit.dart';
import '../../../core/format.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/models.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../auth/presentation/auth_cubit.dart';
import '../data/carbon_repository.dart';

typedef DashboardData = ({
  Map<String, dynamic> dashboard,
  Map<String, dynamic>? summary,
});

class DashboardPage extends StatefulWidget {
  const DashboardPage({super.key});

  @override
  State<DashboardPage> createState() => _DashboardPageState();
}

class _DashboardPageState extends State<DashboardPage> {
  String _period = 'month';
  late AsyncCubit<DashboardData> _cubit;

  @override
  void initState() {
    super.initState();
    _cubit = AsyncCubit<DashboardData>(const AsyncState());
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _cubit.run(_load);
    });
  }

  Future<DashboardData> _load() async {
    final repo = context.read<CarbonRepository>();
    final locale = context.l10n.locale.languageCode;
    final dashboard = await repo.dashboard(period: _period);
    Map<String, dynamic>? summary;
    try {
      summary = await repo.aiSummary(period: _period, locale: locale);
    } catch (_) {
      summary = null;
    }
    return (dashboard: dashboard, summary: summary);
  }

  void _reload() {
    _cubit.run(_load, keepData: true, silent: true);
  }

  void _changePeriod(String period) {
    setState(() => _period = period);
    _cubit.run(_load);
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthCubit>().state.user;
    final firstName = (user?.fullName ?? '').split(' ').first;
    final l10n = context.l10n;
    final greeting = l10n.t(greetingKeyFor(DateTime.now()));

    return Scaffold(
      appBar: AppBar(
        toolbarHeight: 74,
        titleSpacing: 20,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              '$greeting${firstName.isEmpty ? '' : ', $firstName'}',
              style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 2),
            Text(
              l10n.t('dashboardSubtitle'),
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w400,
                color: AppColors.muted,
              ),
            ),
          ],
        ),
        actions: [
          IconButton(
            onPressed: () => context.push('/notifications'),
            icon: const Icon(Icons.notifications_none_rounded),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: RefreshIndicator(
          onRefresh: () async {
            await _cubit.run(_load, silent: true);
          },
          child: AsyncPageBody<DashboardData>(
            onRetry: () => _cubit.run(_load),
            builder: (data) => _DashboardContent(
              data: data,
              period: _period,
              onPeriodChanged: _changePeriod,
              onRefresh: _reload,
            ),
          ),
        ),
      ),
    );
  }
}

class _DashboardContent extends StatelessWidget {
  const _DashboardContent({
    required this.data,
    required this.period,
    required this.onPeriodChanged,
    required this.onRefresh,
  });

  final DashboardData data;
  final String period;
  final ValueChanged<String> onPeriodChanged;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final locale = l10n.locale.languageCode;
    final dashboard = data.dashboard;
    final totals = map(dashboard['totals']);
    final change = map(dashboard['change']);
    final categories = maps(dashboard['categories']);
    final recent = maps(dashboard['recent_records']);
    final goals = maps(dashboard['goals']);
    final top = map(dashboard['top_category']);
    final totalKg = n(totals['emissions_kg']);
    final changePercent = n(change['percent']);
    final direction = s(change['direction'], 'flat');
    final summary = data.summary;

    return ListView(
      physics: const AlwaysScrollableScrollPhysics(),
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
      children: [
        PeriodSelector(value: period, onChanged: onPeriodChanged),
        const SizedBox(height: 16),
        Container(
          padding: const EdgeInsets.all(22),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                AppColors.forestDeep,
                AppColors.forest,
                Color(0xFF2A8465),
              ],
            ),
            borderRadius: BorderRadius.circular(28),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Text(
                    l10n.t('totalEmissions'),
                    style: TextStyle(
                      color: Colors.white.withValues(alpha: 0.7),
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                  const Spacer(),
                  Pill(
                    label:
                        '${direction == 'up' ? '+' : ''}${formatPercent(changePercent, locale: locale)}',
                    color: Colors.white.withValues(alpha: 0.14),
                    foreground: Colors.white,
                    icon: direction == 'down'
                        ? Icons.trending_down_rounded
                        : (direction == 'up'
                              ? Icons.trending_up_rounded
                              : Icons.trending_flat_rounded),
                  ),
                ],
              ),
              const SizedBox(height: 10),
              Directionality(
                textDirection: TextDirection.ltr,
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.end,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      formatKg(totalKg, locale: locale),
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 46,
                        height: 1,
                        fontWeight: FontWeight.w800,
                        letterSpacing: -1.5,
                      ),
                    ),
                    const Padding(
                      padding: EdgeInsets.only(bottom: 6, left: 7),
                      child: Text(
                        'kg CO₂e',
                        style: TextStyle(color: Colors.white70, fontSize: 13),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 8),
              Text(
                l10n.t('vsPrevious'),
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.55),
                  fontSize: 11,
                ),
              ),
              const SizedBox(height: 20),
              Row(
                children: [
                  Expanded(
                    child: _HeroStat(
                      label: l10n.t('recordsLogged'),
                      value: '${ni(totals['records'])}',
                    ),
                  ),
                  Container(
                    width: 1,
                    height: 36,
                    color: Colors.white.withValues(alpha: 0.15),
                  ),
                  Expanded(
                    child: _HeroStat(
                      label: l10n.t('avgPerDay'),
                      value: formatNumber(
                        n(totals['avg_kg_per_day']),
                        locale: locale,
                      ),
                    ),
                  ),
                  Container(
                    width: 1,
                    height: 36,
                    color: Colors.white.withValues(alpha: 0.15),
                  ),
                  Expanded(
                    child: _HeroStat(
                      label: l10n.t('topCategory'),
                      value: top.isEmpty
                          ? '—'
                          : (locale == 'ar'
                                ? s(top['name_ar'])
                                : s(top['name_en'])),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        const SizedBox(height: 22),
        _QuickActions(onRefresh: onRefresh),
        const SizedBox(height: 26),
        SectionTitle(
          l10n.t('aiInsight'),
          action: l10n.t('viewAll'),
          onAction: () => context.push('/insights'),
        ),
        if (summary != null)
          _InsightCard(summary: summary, onRefresh: onRefresh)
        else
          CarbonCard(
            child: Row(
              children: [
                const CategoryAvatar(category: null, size: 38),
                const SizedBox(width: 12),
                Expanded(
                  child: Text(
                    l10n.t('aiDisabledBody'),
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.muted,
                    ),
                  ),
                ),
              ],
            ),
          ),
        const SizedBox(height: 26),
        SectionTitle(
          l10n.t('byCategory'),
          action: l10n.t('reports'),
          onAction: () => context.go('/reports'),
        ),
        CarbonCard(
          child: categories.isEmpty
              ? Text(
                  l10n.t('noReports'),
                  style: const TextStyle(color: AppColors.muted, fontSize: 12),
                )
              : Column(
                  children: [
                    for (var i = 0; i < categories.length; i++) ...[
                      _CategoryRow(
                        row: categories[i],
                        locale: locale,
                        isLast: i == categories.length - 1,
                      ),
                      if (i != categories.length - 1)
                        const SizedBox(height: 15),
                    ],
                  ],
                ),
        ),
        if (goals.isNotEmpty) ...[
          const SizedBox(height: 26),
          SectionTitle(
            l10n.t('goalProgress'),
            action: l10n.t('viewAll'),
            onAction: () => context.push('/goals'),
          ),
          for (final goal in goals.take(2)) ...[
            _GoalCard(goal: map(goal), locale: locale),
            const SizedBox(height: 10),
          ],
        ],
        const SizedBox(height: 22),
        SectionTitle(
          l10n.t('recentActivity'),
          action: l10n.t('viewAll'),
          onAction: () => context.go('/records'),
        ),
        if (recent.isEmpty)
          EmptyState(
            message: l10n.t('noRecords'),
            actionLabel: l10n.t('addRecord'),
            onAction: () => context.push('/records/new'),
          )
        else
          CarbonCard(
            padding: const EdgeInsets.symmetric(vertical: 4),
            child: Column(
              children: [
                for (var i = 0; i < recent.length; i++) ...[
                  _RecentRow(record: map(recent[i]), locale: locale),
                  if (i != recent.length - 1)
                    const Divider(height: 1, indent: 64, endIndent: 18),
                ],
              ],
            ),
          ),
      ],
    );
  }
}

class _HeroStat extends StatelessWidget {
  const _HeroStat({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 10),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            value,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 15,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 3),
          Text(
            label,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: TextStyle(
              color: Colors.white.withValues(alpha: 0.55),
              fontSize: 9.5,
            ),
          ),
        ],
      ),
    );
  }
}

class _QuickActions extends StatelessWidget {
  const _QuickActions({required this.onRefresh});

  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final items = [
      (
        Icons.add_rounded,
        l10n.t('addRecord'),
        '/records/new',
        AppColors.forest,
      ),
      (Icons.flag_outlined, l10n.t('goals'), '/goals', const Color(0xFF3F6FA8)),
      (
        Icons.route_outlined,
        l10n.t('plans'),
        '/plans',
        const Color(0xFF8C5A2B),
      ),
      (
        Icons.auto_awesome_rounded,
        l10n.t('assistant'),
        '/assistant',
        const Color(0xFF5B4B8A),
      ),
    ];
    return Row(
      children: [
        for (var i = 0; i < items.length; i++) ...[
          Expanded(
            child: InkWell(
              borderRadius: BorderRadius.circular(16),
              onTap: () async {
                await context.push(items[i].$3);
                onRefresh();
              },
              child: Container(
                padding: const EdgeInsets.symmetric(
                  vertical: 13,
                  horizontal: 6,
                ),
                decoration: BoxDecoration(
                  color: AppColors.paper,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppColors.line),
                ),
                child: Column(
                  children: [
                    Icon(items[i].$1, color: items[i].$4, size: 22),
                    const SizedBox(height: 6),
                    Text(
                      items[i].$2,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 9.5,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
          if (i != items.length - 1) const SizedBox(width: 8),
        ],
      ],
    );
  }
}

class _InsightCard extends StatelessWidget {
  const _InsightCard({required this.summary, required this.onRefresh});

  final Map<String, dynamic> summary;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final source = s(summary['source'], 'rules');
    return CarbonCard(
      color: AppColors.mint,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(
                Icons.auto_awesome_rounded,
                size: 18,
                color: AppColors.forest,
              ),
              const SizedBox(width: 8),
              Pill(
                label: source == 'ai'
                    ? 'AI · openrouter/free'
                    : l10n.t('aiRules'),
                color: AppColors.paper,
                foreground: AppColors.forest,
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            s(summary['narrative']),
            maxLines: 5,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontSize: 12.5,
              height: 1.55,
              color: AppColors.ink,
            ),
          ),
          const SizedBox(height: 10),
          Row(
            children: [
              TextButton(
                onPressed: () => context.push('/insights'),
                child: Text(l10n.t('viewDetails')),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _CategoryRow extends StatelessWidget {
  const _CategoryRow({
    required this.row,
    required this.locale,
    required this.isLast,
  });

  final Map<String, dynamic> row;
  final String locale;
  final bool isLast;

  @override
  Widget build(BuildContext context) {
    final category = Category(
      id: ni(row['category_id']),
      key: s(row['key']),
      nameEn: s(row['name_en']),
      nameAr: s(row['name_ar']),
      icon: '',
      colorHex: '',
      unitHint: '',
    );
    final share = n(row['share_percent']) / 100;
    return Row(
      children: [
        CategoryAvatar(category: category, size: 36),
        const SizedBox(width: 11),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Expanded(
                    child: Text(
                      category.name(locale),
                      style: const TextStyle(
                        fontSize: 12.5,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  Text(
                    '${formatKg(n(row['emissions_kg']), locale: locale)} ${context.tr('kg')}',
                    style: const TextStyle(
                      fontSize: 11.5,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 7),
              MetricBar(value: share),
            ],
          ),
        ),
      ],
    );
  }
}

class _GoalCard extends StatelessWidget {
  const _GoalCard({required this.goal, required this.locale});

  final Map<String, dynamic> goal;
  final String locale;

  @override
  Widget build(BuildContext context) {
    final achieved = n(goal['achieved_percent']);
    return CarbonCard(
      onTap: () => context.push('/goals/${goal['id']}'),
      padding: const EdgeInsets.all(16),
      child: Row(
        children: [
          SizedBox(
            width: 48,
            height: 48,
            child: Stack(
              alignment: Alignment.center,
              children: [
                CircularProgressIndicator(
                  value: achieved / 100,
                  strokeWidth: 5,
                  backgroundColor: AppColors.line,
                  strokeCap: StrokeCap.round,
                ),
                Text(
                  '${achieved.round()}',
                  style: const TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  s(goal['title']),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  '${formatKg(n(goal['current_emissions_kg']), locale: locale)} / ${formatKg(n(goal['target_emissions_kg']), locale: locale)} kg',
                  style: const TextStyle(
                    fontSize: 10.5,
                    color: AppColors.muted,
                  ),
                ),
              ],
            ),
          ),
          Pill(
            label: formatPercent(achieved, locale: locale),
            color: AppColors.mint,
            foreground: AppColors.forest,
          ),
        ],
      ),
    );
  }
}

class _RecentRow extends StatelessWidget {
  const _RecentRow({required this.record, required this.locale});

  final Map<String, dynamic> record;
  final String locale;

  @override
  Widget build(BuildContext context) {
    final categoryJson = record['category'];
    final category = categoryJson is Map
        ? Category.fromJson(map(categoryJson))
        : null;
    final date = DateTime.tryParse(s(record['activity_date']));
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      child: Row(
        children: [
          CategoryAvatar(category: category, size: 38),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  category?.name(locale) ?? '—',
                  style: const TextStyle(
                    fontSize: 12.5,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                const SizedBox(height: 2),
                Text(
                  '${formatKg(n(record['quantity']), locale: locale)} ${s(record['unit'])} · ${formatDate(date, locale: locale)}',
                  style: const TextStyle(fontSize: 10, color: AppColors.muted),
                ),
              ],
            ),
          ),
          Text(
            '${formatKg(n(record['emissions_kg']), locale: locale)} kg',
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w800),
          ),
        ],
      ),
    );
  }
}
