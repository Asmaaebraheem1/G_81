import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/async_cubit.dart';
import '../../../core/format.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/models.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../dashboard/data/carbon_repository.dart';

class InsightsPage extends StatefulWidget {
  const InsightsPage({super.key});

  @override
  State<InsightsPage> createState() => _InsightsPageState();
}

class _InsightsPageState extends State<InsightsPage> {
  String _period = 'month';
  late AsyncCubit<Map<String, dynamic>> _cubit;

  Future<Map<String, dynamic>> _load() =>
      context.read<CarbonRepository>().aiInsights(
            period: _period,
            locale: context.l10n.locale.languageCode,
          );

  @override
  void initState() {
    super.initState();
    _cubit = AsyncCubit<Map<String, dynamic>>(const AsyncState());
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _cubit.run(_load);
    });
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
              l10n.t('insightsTitle'),
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 2),
            Text(
              l10n.t('insightsSubtitle'),
              style: const TextStyle(fontSize: 11.5, color: AppColors.muted),
            ),
          ],
        ),
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: AsyncPageBody<Map<String, dynamic>>(
          onRetry: () => _cubit.run(_load),
          builder: (data) {
            final locale = l10n.locale.languageCode;
            final source = s(data['source'], 'rules');
            final contextData = map(data['calculated_context']);
            final sources = maps(data['top_sources']);
            final opportunities = maps(data['opportunities']);
            final observations = data['observations'] is List
                ? (data['observations'] as List).map((e) => s(e)).toList()
                : const <String>[];
            return ListView(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
              children: [
                PeriodSelector(
                  value: _period,
                  onChanged: (period) {
                    setState(() => _period = period);
                    _cubit.run(_load);
                  },
                ),
                const SizedBox(height: 16),
                CarbonCard(
                  color: AppColors.mint,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          const Icon(Icons.auto_awesome_rounded, size: 18, color: AppColors.forest),
                          const SizedBox(width: 8),
                          Pill(
                            label: source == 'ai' ? 'AI · openrouter/free' : l10n.t('aiRules'),
                          ),
                        ],
                      ),
                      const SizedBox(height: 12),
                      BidiText(
                        s(data['narrative']),
                        style: const TextStyle(fontSize: 13, height: 1.55),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 22),
                Row(
                  children: [
                    Expanded(
                      child: _MetricTile(
                        label: l10n.t('totalEmissions'),
                        value: '${formatKg(n(contextData['total_kg']), locale: locale)} ${l10n.t('kg')}',
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: _MetricTile(
                        label: l10n.t('vsPrevious'),
                        value: '${formatPercent(n(contextData['change_percent']), locale: locale)}',
                      ),
                    ),
                  ],
                ),
                if (observations.isNotEmpty) ...[
                  const SizedBox(height: 24),
                  SectionTitle(l10n.t('insightsTitle')),
                  CarbonCard(
                    child: Column(
                      children: [
                        for (final observation in observations)
                          Padding(
                            padding: const EdgeInsets.symmetric(vertical: 6),
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Icon(Icons.circle, size: 6, color: AppColors.forest),
                                const SizedBox(width: 10),
                                Expanded(
                                  child: BidiText(
                                    observation,
                                    style: const TextStyle(fontSize: 11.5, height: 1.45),
                                  ),
                                ),
                              ],
                            ),
                          ),
                      ],
                    ),
                  ),
                ],
                const SizedBox(height: 24),
                SectionTitle(l10n.t('topSources')),
                CarbonCard(
                  child: sources.isEmpty
                      ? Text(
                          l10n.t('noReports'),
                          style: const TextStyle(color: AppColors.muted, fontSize: 12),
                        )
                      : Column(
                          children: [
                            for (var i = 0; i < sources.length; i++) ...[
                              Row(
                                children: [
                                  Expanded(
                                    child: Text(
                                      locale == 'ar'
                                          ? s(sources[i]['name_ar'])
                                          : s(sources[i]['name_en']),
                                      style: const TextStyle(fontSize: 11.5),
                                    ),
                                  ),
                                  Text(
                                    '${formatKg(n(sources[i]['emissions_kg']), locale: locale)} ${l10n.t('kg')}',
                                    textDirection: TextDirection.ltr,
                                    style: const TextStyle(
                                      fontSize: 10.5,
                                      color: AppColors.muted,
                                    ),
                                  ),
                                  const SizedBox(width: 8),
                                  Text(
                                    formatPercent(n(sources[i]['share_percent']), locale: locale),
                                    style: const TextStyle(
                                      fontSize: 10.5,
                                      fontWeight: FontWeight.w700,
                                    ),
                                  ),
                                ],
                              ),
                              const SizedBox(height: 6),
                              MetricBar(value: n(sources[i]['share_percent']) / 100),
                              if (i != sources.length - 1) const SizedBox(height: 13),
                            ],
                          ],
                        ),
                ),
                const SizedBox(height: 24),
                SectionTitle(l10n.t('opportunities')),
                if (opportunities.isEmpty)
                  CarbonCard(
                    child: Text(
                      l10n.isArabic
                          ? 'لا توجد فرص من الكتالوج لهذه الفترة.'
                          : 'No catalog opportunities for this period yet.',
                      style: const TextStyle(fontSize: 11.5, color: AppColors.muted),
                    ),
                  )
                else
                  for (final opportunity in opportunities.take(4)) ...[
                    CarbonCard(
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Container(
                            width: 32,
                            height: 32,
                            decoration: const BoxDecoration(
                              color: AppColors.sandSoft,
                              shape: BoxShape.circle,
                            ),
                            child: const Icon(
                              Icons.tips_and_updates_outlined,
                              size: 16,
                              color: Color(0xFF8C5A2B),
                            ),
                          ),
                          const SizedBox(width: 11),
                          Expanded(
                            child: Text(
                              locale == 'ar'
                                  ? s(opportunity['title_ar'])
                                  : s(opportunity['title_en']),
                              style: const TextStyle(fontSize: 11.5, height: 1.4),
                            ),
                          ),
                          if (s(opportunity['source']) == 'ai_text')
                            Pill(label: context.tr('aiText')),
                        ],
                      ),
                    ),
                    const SizedBox(height: 8),
                  ],
                const SizedBox(height: 16),
                Text(
                  s(data['disclaimer']),
                  style: const TextStyle(fontSize: 9.5, color: AppColors.muted, height: 1.45),
                ),
              ],
            );
          },
        ),
      ),
    );
  }
}

class _MetricTile extends StatelessWidget {
  const _MetricTile({required this.label, required this.value});

  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return CarbonCard(
      padding: const EdgeInsets.all(15),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(fontSize: 9.5, color: AppColors.muted),
          ),
          const SizedBox(height: 5),
          Text(
            value,
            textDirection: TextDirection.ltr,
            style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
          ),
        ],
      ),
    );
  }
}
