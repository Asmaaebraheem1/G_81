import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/async_cubit.dart';
import '../../../core/format.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/models.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../dashboard/data/carbon_repository.dart';

typedef AlternativesData = ({
  Map<String, dynamic> recommended,
  List<Map<String, dynamic>> saved,
});

class AlternativesPage extends StatefulWidget {
  const AlternativesPage({super.key});

  @override
  State<AlternativesPage> createState() => _AlternativesPageState();
}

class _AlternativesPageState extends State<AlternativesPage> {
  late AsyncCubit<AlternativesData> _cubit;

  Future<AlternativesData> _load() async {
    final repo = context.read<CarbonRepository>();
    final results = await Future.wait([
      repo.recommendedAlternatives(locale: context.l10n.locale.languageCode),
      repo.savedAlternatives(),
    ]);
    return (
      recommended: results[0] as Map<String, dynamic>,
      saved: results[1] as List<Map<String, dynamic>>,
    );
  }

  @override
  void initState() {
    super.initState();
    _cubit = AsyncCubit<AlternativesData>(const AsyncState());
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) _cubit.run(_load);
    });
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  Future<void> _setStatus(int id, String status) async {
    try {
      await context.read<CarbonRepository>().saveAlternative(id, status);
      if (!mounted) return;
      showSnack(context, context.tr('saved'));
      _cubit.run(_load, silent: true);
    } catch (error) {
      if (!mounted) return;
      showSnack(context, error.toString(), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: Text(
            l10n.t('alternativesTitle'),
            style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
          ),
          bottom: TabBar(
            labelColor: AppColors.forest,
            unselectedLabelColor: AppColors.muted,
            indicatorColor: AppColors.forest,
            tabs: [
              Tab(text: l10n.t('recommended')),
              Tab(text: l10n.t('saved')),
            ],
          ),
        ),
        body: BlocProvider.value(
          value: _cubit,
          child: AsyncPageBody<AlternativesData>(
            onRetry: () => _cubit.run(_load),
            builder: (data) => TabBarView(
              children: [
                _RecommendedTab(data: data, onStatus: _setStatus),
                _SavedTab(saved: data.saved, onStatus: _setStatus),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _RecommendedTab extends StatelessWidget {
  const _RecommendedTab({required this.data, required this.onStatus});

  final AlternativesData data;
  final void Function(int id, String status) onStatus;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final items = maps(data.recommended['alternatives']);
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 30),
      children: [
        if (s(data.recommended['rationale']).isNotEmpty)
          Container(
            padding: const EdgeInsets.all(13),
            margin: const EdgeInsets.only(bottom: 14),
            decoration: BoxDecoration(
              color: AppColors.mint,
              borderRadius: BorderRadius.circular(16),
            ),
            child: Text(
              s(data.recommended['rationale']),
              style: const TextStyle(fontSize: 10.5, height: 1.45, color: AppColors.forest),
            ),
          ),
        if (items.isEmpty)
          EmptyState(message: l10n.t('noData'), icon: Icons.swap_horiz_rounded)
        else
          for (final item in items) ...[
            _AlternativeCard(
              alternative: Alternative.fromJson(item),
              onStatus: onStatus,
            ),
            const SizedBox(height: 11),
          ],
        if (items.isNotEmpty)
          Text(
            s(data.recommended['note']),
            style: const TextStyle(fontSize: 9.5, color: AppColors.muted, height: 1.45),
          ),
      ],
    );
  }
}

class _SavedTab extends StatelessWidget {
  const _SavedTab({required this.saved, required this.onStatus});

  final List<Map<String, dynamic>> saved;
  final void Function(int id, String status) onStatus;

  @override
  Widget build(BuildContext context) {
    if (saved.isEmpty) {
      return EmptyState(message: context.tr('noData'), icon: Icons.bookmark_border_rounded);
    }
    return ListView.separated(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 30),
      itemCount: saved.length,
      separatorBuilder: (_, _) => const SizedBox(height: 11),
      itemBuilder: (context, index) {
        final row = saved[index];
        final nested = map(row['alternative']);
        final alternative = Alternative.fromJson({
          ...nested,
          'saved_status': s(row['status']),
        });
        return _AlternativeCard(
          alternative: alternative,
          onStatus: onStatus,
        );
      },
    );
  }
}

class _AlternativeCard extends StatelessWidget {
  const _AlternativeCard({required this.alternative, required this.onStatus});

  final Alternative alternative;
  final void Function(int id, String status) onStatus;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final locale = l10n.locale.languageCode;
    final status = alternative.savedStatus;
    return CarbonCard(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                width: 40,
                height: 40,
                decoration: const BoxDecoration(
                  color: AppColors.mint,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.swap_horiz_rounded, color: AppColors.forest, size: 20),
              ),
              const SizedBox(width: 11),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    BidiText(
                      alternative.title(locale),
                      style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
                    ),
                    const SizedBox(height: 3),
                    BidiText(
                      alternative.description(locale),
                      style: const TextStyle(fontSize: 10.5, height: 1.45, color: AppColors.muted),
                    ),
                  ],
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
                decoration: BoxDecoration(
                  color: AppColors.sandSoft,
                  borderRadius: BorderRadius.circular(11),
                ),
                child: Text(
                  '−${formatNumber(alternative.estimatedReductionPercent)}%',
                  textDirection: TextDirection.ltr,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w800,
                    color: Color(0xFF8C5A2B),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (alternative.assumption(locale).trim().isNotEmpty &&
              alternative.assumption(locale).trim() != alternative.description(locale).trim())
            BidiText(
              '${l10n.t('assumption')}: ${alternative.assumption(locale)}',
              style: const TextStyle(fontSize: 9.5, height: 1.4, color: AppColors.muted),
            ),
          const SizedBox(height: 5),
          BidiText(
            '${l10n.t('source')}: '
            '${alternative.source == 'ai' ? l10n.t('aiRecommendation') : l10n.t('curatedAssumption')}',
            style: const TextStyle(fontSize: 9.5, color: AppColors.muted),
          ),
          const SizedBox(height: 12),
          Row(
            children: [
              if (status == null || status == 'saved')
                Expanded(
                  child: FilledButton(
                    onPressed: () => onStatus(alternative.id, 'accepted'),
                    style: FilledButton.styleFrom(
                      minimumSize: const Size(0, 40),
                      textStyle: const TextStyle(fontSize: 11, fontWeight: FontWeight.w700),
                    ),
                    child: Text(l10n.t('accept')),
                  ),
                )
              else
                Expanded(
                  child: Pill(
                    label: status == 'accepted' ? l10n.t('accept') : l10n.t('dismiss'),
                    icon: status == 'accepted' ? Icons.check_rounded : Icons.close_rounded,
                  ),
                ),
              const SizedBox(width: 8),
              OutlinedButton(
                onPressed: () => onStatus(alternative.id, 'dismissed'),
                style: OutlinedButton.styleFrom(
                  minimumSize: const Size(0, 40),
                  textStyle: const TextStyle(fontSize: 11),
                ),
                child: Text(l10n.t('dismiss')),
              ),
            ],
          ),
        ],
      ),
    );
  }
}
