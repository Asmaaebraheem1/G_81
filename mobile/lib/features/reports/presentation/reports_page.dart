import 'dart:io';

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:path_provider/path_provider.dart';

import '../../../core/async_cubit.dart';
import '../../../core/format.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/models.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../dashboard/data/carbon_repository.dart';

typedef ReportsData = ({
  Map<String, dynamic> summary,
  List<Map<String, dynamic>> trend,
  Map<String, dynamic> comparison,
  List<Map<String, dynamic>> top,
});

class ReportsPage extends StatefulWidget {
  const ReportsPage({super.key});

  @override
  State<ReportsPage> createState() => _ReportsPageState();
}

class _ReportsPageState extends State<ReportsPage> {
  String _period = 'month';
  bool _exporting = false;
  late AsyncCubit<ReportsData> _cubit;

  @override
  void initState() {
    super.initState();
    _cubit = AsyncCubit<ReportsData>(const AsyncState())..run(_load);
  }

  Future<ReportsData> _load() async {
    final repo = context.read<CarbonRepository>();
    final results = await Future.wait([
      repo.dashboard(period: _period),
      repo.trend(months: 6),
      repo.comparison(period: _period),
      repo.topActivities(period: _period, limit: 5),
    ]);
    return (
      summary: results[0] as Map<String, dynamic>,
      trend: results[1] as List<Map<String, dynamic>>,
      comparison: results[2] as Map<String, dynamic>,
      top: results[3] as List<Map<String, dynamic>>,
    );
  }

  void _changePeriod(String period) {
    setState(() => _period = period);
    _cubit.run(_load);
  }

  Future<void> _export() async {
    setState(() => _exporting = true);
    try {
      final summary = _cubit.state.data?.summary;
      final period = map(summary?['period']);
      final from = s(period['from']);
      final to = s(period['to']);
      final bytes = await context.read<CarbonRepository>().exportCsv(from: from, to: to);
      final directory = await getApplicationDocumentsDirectory();
      final file = File('${directory.path}/carbonwise-$from-$to.csv');
      await file.writeAsBytes(bytes, flush: true);
      if (!mounted) return;
      showSnack(context, '${context.tr('exported')}\n${file.path}');
    } catch (error) {
      if (!mounted) return;
      showSnack(context, error.toString(), error: true);
    } finally {
      if (mounted) setState(() => _exporting = false);
    }
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return Scaffold(
      appBar: AppBar(
        titleSpacing: 20,
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              l10n.t('reportsTitle'),
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 2),
            Text(
              l10n.t('reportsSubtitle'),
              style: const TextStyle(fontSize: 11.5, color: AppColors.muted),
            ),
          ],
        ),
        actions: [
          IconButton(
            onPressed: _exporting ? null : _export,
            icon: _exporting
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.download_outlined),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: AsyncPageBody<ReportsData>(
          onRetry: () => _cubit.run(_load),
          builder: (data) => ListView(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
            children: [
              PeriodSelector(value: _period, onChanged: _changePeriod),
              const SizedBox(height: 16),
              _SummaryCard(summary: data.summary, period: _period),
              const SizedBox(height: 26),
              SectionTitle(l10n.t('trend')),
              CarbonCard(
                child: data.trend.every((point) => ni(point['emissions_grams']) == 0)
                    ? Text(
                        l10n.t('noReports'),
                        style: const TextStyle(color: AppColors.muted, fontSize: 12),
                      )
                    : _TrendChart(points: data.trend),
              ),
              const SizedBox(height: 26),
              SectionTitle(l10n.t('byCategory')),
              CarbonCard(
                child: _CategoryBreakdown(
                  categories: maps(data.summary['categories']),
                ),
              ),
              const SizedBox(height: 26),
              SectionTitle(l10n.t('comparison')),
              _ComparisonCard(comparison: data.comparison),
              const SizedBox(height: 26),
              SectionTitle(l10n.t('topActivities')),
              if (data.top.isEmpty)
                CarbonCard(
                  child: Text(
                    l10n.t('noReports'),
                    style: const TextStyle(color: AppColors.muted, fontSize: 12),
                  ),
                )
              else
                CarbonCard(
                  padding: const EdgeInsets.symmetric(vertical: 4),
                  child: Column(
                    children: [
                      for (var i = 0; i < data.top.length; i++) ...[
                        _TopActivityRow(index: i + 1, row: data.top[i]),
                        if (i != data.top.length - 1)
                          const Divider(height: 1, indent: 52, endIndent: 16),
                      ],
                    ],
                  ),
                ),
            ],
          ),
        ),
      ),
    );
  }
}

class _SummaryCard extends StatelessWidget {
  const _SummaryCard({required this.summary, required this.period});

  final Map<String, dynamic> summary;
  final String period;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final locale = l10n.locale.languageCode;
    final totals = map(summary['totals']);
    final change = map(summary['change']);
    final direction = s(change['direction'], 'flat');
    return CarbonCard(
      color: AppColors.forestDeep,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                l10n.t('totalEmissions'),
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.6),
                  fontSize: 11,
                ),
              ),
              const Spacer(),
              Pill(
                label: period == 'month'
                    ? l10n.t('thisMonth')
                    : l10n.t('last30Days'),
                color: Colors.white.withValues(alpha: 0.12),
                foreground: Colors.white,
              ),
            ],
          ),
          const SizedBox(height: 9),
          Text(
            '${formatKg(n(totals['emissions_kg']), locale: locale)} kg',
            textDirection: TextDirection.ltr,
            textAlign: TextAlign.right,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 36,
              fontWeight: FontWeight.w800,
              letterSpacing: -1,
            ),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              Icon(
                direction == 'down'
                    ? Icons.trending_down_rounded
                    : direction == 'up'
                        ? Icons.trending_up_rounded
                        : Icons.trending_flat_rounded,
                color: direction == 'down' ? AppColors.mint : AppColors.sandSoft,
                size: 17,
              ),
              const SizedBox(width: 6),
              Text(
                '${formatPercent(n(change['percent']).abs(), locale: locale)} '
                '${direction == 'down' ? l10n.t('lower') : (direction == 'up' ? l10n.t('higher') : l10n.t('same'))} · ${l10n.t('vsPrevious')}',
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.65),
                  fontSize: 10.5,
                ),
              ),
            ],
          ),
          const SizedBox(height: 18),
          Row(
            children: [
              _MiniStat(
                value: '${ni(totals['records'])}',
                label: l10n.t('recordsLogged'),
              ),
              const SizedBox(width: 30),
              _MiniStat(
                value: formatNumber(n(totals['avg_kg_per_day']), locale: locale),
                label: l10n.t('avgPerDay'),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

class _MiniStat extends StatelessWidget {
  const _MiniStat({required this.value, required this.label});

  final String value;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          value,
          style: const TextStyle(
            color: Colors.white,
            fontSize: 16,
            fontWeight: FontWeight.w800,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          label,
          style: TextStyle(
            color: Colors.white.withValues(alpha: 0.5),
            fontSize: 9,
          ),
        ),
      ],
    );
  }
}

class _TrendChart extends StatelessWidget {
  const _TrendChart({required this.points});

  final List<Map<String, dynamic>> points;

  @override
  Widget build(BuildContext context) {
    final max = points.fold<double>(1, (value, point) => n(point['emissions_kg']) > value ? n(point['emissions_kg']) : value);
    final locale = context.l10n.locale.languageCode;
    return Column(
      children: [
        SizedBox(
          height: 166,
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              for (var i = 0; i < points.length; i++) ...[
                Expanded(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      Text(
                        formatKg(n(points[i]['emissions_kg']), locale: locale),
                        style: const TextStyle(fontSize: 8, color: AppColors.muted),
                      ),
                      const SizedBox(height: 4),
                      TweenAnimationBuilder<double>(
                        tween: Tween(begin: 0, end: n(points[i]['emissions_kg']) / max),
                        duration: Duration(milliseconds: 500 + i * 90),
                        curve: Curves.easeOutCubic,
                        builder: (context, value, _) => Container(
                          height: 118 * value.clamp(0.02, 1),
                          margin: const EdgeInsets.symmetric(horizontal: 7),
                          decoration: BoxDecoration(
                            color: i == points.length - 1 ? AppColors.forest : AppColors.mint,
                            borderRadius: BorderRadius.circular(7),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            for (final point in points)
              Expanded(
                child: Text(
                  _monthLabel(point['month'], locale),
                  textAlign: TextAlign.center,
                  style: const TextStyle(fontSize: 8.5, color: AppColors.muted),
                ),
              ),
          ],
        ),
      ],
    );
  }

  String _monthLabel(dynamic month, String locale) {
    final parsed = DateTime.tryParse('${s(month)}-01');
    return parsed == null ? s(month) : formatDate(parsed, locale: locale, pattern: 'MMM');
  }
}

class _CategoryBreakdown extends StatelessWidget {
  const _CategoryBreakdown({required this.categories});

  final List<Map<String, dynamic>> categories;

  @override
  Widget build(BuildContext context) {
    if (categories.isEmpty) {
      return Text(
        context.tr('noReports'),
        style: const TextStyle(color: AppColors.muted, fontSize: 12),
      );
    }
    final locale = context.l10n.locale.languageCode;
    return Column(
      children: [
        for (var i = 0; i < categories.length; i++) ...[
          Row(
            children: [
              Expanded(
                child: Text(
                  locale == 'ar' ? s(categories[i]['name_ar']) : s(categories[i]['name_en']),
                  style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w600),
                ),
              ),
              Text(
                '${formatKg(n(categories[i]['emissions_kg']), locale: locale)} kg',
                textDirection: TextDirection.ltr,
                style: const TextStyle(fontSize: 10.5, color: AppColors.muted),
              ),
              const SizedBox(width: 8),
              SizedBox(
                width: 32,
                child: Text(
                  formatPercent(n(categories[i]['share_percent']), locale: locale),
                  textAlign: TextAlign.end,
                  style: const TextStyle(fontSize: 10.5, fontWeight: FontWeight.w700),
                ),
              ),
            ],
          ),
          const SizedBox(height: 6),
          MetricBar(value: n(categories[i]['share_percent']) / 100),
          if (i != categories.length - 1) const SizedBox(height: 14),
        ],
      ],
    );
  }
}

class _ComparisonCard extends StatelessWidget {
  const _ComparisonCard({required this.comparison});

  final Map<String, dynamic> comparison;

  @override
  Widget build(BuildContext context) {
    final locale = context.l10n.locale.languageCode;
    final rows = maps(comparison['categories']);
    return CarbonCard(
      child: Column(
        children: [
          for (var i = 0; i < rows.length; i++) ...[
            Row(
              children: [
                Expanded(
                  child: Text(
                    locale == 'ar' ? s(rows[i]['name_ar']) : s(rows[i]['name_en']),
                    style: const TextStyle(fontSize: 11.5),
                  ),
                ),
                Text(
                  '${formatKg(n(rows[i]['current_grams']) / 1000, locale: locale)} / '
                  '${formatKg(n(rows[i]['previous_grams']) / 1000, locale: locale)} kg',
                  style: const TextStyle(fontSize: 10, color: AppColors.muted),
                ),
                const SizedBox(width: 8),
                Pill(
                  label: '${n(rows[i]['change_percent']) > 0 ? '+' : ''}'
                      '${formatPercent(n(rows[i]['change_percent']), locale: locale)}',
                  color: n(rows[i]['change_percent']) > 0
                      ? const Color(0xFFF7E1DB)
                      : AppColors.mint,
                  foreground: n(rows[i]['change_percent']) > 0
                      ? AppColors.danger
                      : AppColors.forest,
                ),
              ],
            ),
            if (i != rows.length - 1) const Divider(height: 22),
          ],
          if (rows.isEmpty)
            Text(
              context.tr('noReports'),
              style: const TextStyle(color: AppColors.muted, fontSize: 12),
            ),
        ],
      ),
    );
  }
}

class _TopActivityRow extends StatelessWidget {
  const _TopActivityRow({required this.index, required this.row});

  final int index;
  final Map<String, dynamic> row;

  @override
  Widget build(BuildContext context) {
    final locale = context.l10n.locale.languageCode;
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      child: Row(
        children: [
          Container(
            width: 26,
            height: 26,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: index <= 3 ? AppColors.sandSoft : AppColors.cream,
              borderRadius: BorderRadius.circular(9),
            ),
            child: Text(
              '$index',
              style: const TextStyle(fontSize: 10, fontWeight: FontWeight.w800),
            ),
          ),
          const SizedBox(width: 11),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  locale == 'ar' ? s(row['name_ar']) : s(row['name_en']),
                  style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 2),
                Text(
                  '${s(row['records'])} ${context.tr('records')} · ${s(row['unit'])}',
                  style: const TextStyle(fontSize: 9.5, color: AppColors.muted),
                ),
              ],
            ),
          ),
          Text(
            '${formatKg(n(row['emissions_kg']), locale: locale)} kg',
            style: const TextStyle(fontSize: 11.5, fontWeight: FontWeight.w800),
          ),
        ],
      ),
    );
  }
}
