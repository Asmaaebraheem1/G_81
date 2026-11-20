import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';

import '../../../core/async_cubit.dart';
import '../../../core/format.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/models.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../dashboard/data/carbon_repository.dart';

typedef RecordsData = ({
  List<ActivityRecord> records,
  List<Category> categories,
  Map<String, dynamic> meta,
});

class RecordsPage extends StatefulWidget {
  const RecordsPage({super.key});

  @override
  State<RecordsPage> createState() => _RecordsPageState();
}

class _RecordsPageState extends State<RecordsPage> {
  int? _categoryId;
  late AsyncCubit<RecordsData> _cubit;

  @override
  void initState() {
    super.initState();
    _cubit = AsyncCubit<RecordsData>(const AsyncState())..run(_load);
  }

  Future<RecordsData> _load() async {
    final repo = context.read<CarbonRepository>();
    final categories = await repo.categories();
    final page = await repo.records(categoryId: _categoryId, perPage: 50);
    return (records: page.items, categories: categories, meta: page.meta);
  }

  void _reload() {
    _cubit.run(_load, silent: true);
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
              l10n.t('recordsTitle'),
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 2),
            Text(
              l10n.t('recordsSubtitle'),
              style: const TextStyle(fontSize: 11.5, color: AppColors.muted),
            ),
          ],
        ),
        actions: [
          IconButton(
            onPressed: () async {
              await context.push('/records/new');
              _reload();
            },
            icon: const Icon(Icons.add_circle_outline_rounded),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: RefreshIndicator(
          onRefresh: () => _cubit.run(_load, silent: true),
          child: AsyncPageBody<RecordsData>(
            onRetry: () => _cubit.run(_load),
            builder: (data) => Column(
              children: [
                SizedBox(
                  height: 46,
                  child: ListView(
                    scrollDirection: Axis.horizontal,
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    children: [
                      ChoiceChip(
                        label: Text(l10n.t('all')),
                        selected: _categoryId == null,
                        showCheckmark: false,
                        onSelected: (_) {
                          setState(() => _categoryId = null);
                          _cubit.run(_load);
                        },
                      ),
                      for (final category in data.categories) ...[
                        const SizedBox(width: 8),
                        ChoiceChip(
                          label: Text(category.name(l10n.locale.languageCode)),
                          selected: _categoryId == category.id,
                          showCheckmark: false,
                          onSelected: (_) {
                            setState(() => _categoryId = category.id);
                            _cubit.run(_load);
                          },
                        ),
                      ],
                    ],
                  ),
                ),
                const SizedBox(height: 10),
                Expanded(
                  child: data.records.isEmpty
                      ? EmptyState(
                          message: l10n.t('noRecords'),
                          actionLabel: l10n.t('newRecord'),
                          onAction: () async {
                            await context.push('/records/new');
                            _reload();
                          },
                        )
                      : ListView.separated(
                          padding: const EdgeInsets.fromLTRB(20, 8, 20, 28),
                          itemCount: data.records.length + 1,
                          separatorBuilder: (_, _) => const SizedBox(height: 10),
                          itemBuilder: (context, index) {
                            if (index == 0) {
                              return Text(
                                '${ni(data.meta['total'], data.records.length)} ${l10n.t('records')}',
                                style: const TextStyle(
                                  fontSize: 11,
                                  color: AppColors.muted,
                                  fontWeight: FontWeight.w600,
                                ),
                              );
                            }
                            final record = data.records[index - 1];
                            return _RecordCard(record: record, onReturn: _reload);
                          },
                        ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

class _RecordCard extends StatelessWidget {
  const _RecordCard({required this.record, required this.onReturn});

  final ActivityRecord record;
  final VoidCallback onReturn;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final locale = l10n.locale.languageCode;
    return CarbonCard(
      padding: const EdgeInsets.all(15),
      onTap: () async {
        await context.push('/records/${record.id}');
        onReturn();
      },
      child: Row(
        children: [
          CategoryAvatar(category: record.category, size: 44),
          const SizedBox(width: 13),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  record.category?.name(locale) ?? '—',
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
                ),
                const SizedBox(height: 3),
                Text(
                  '${formatKg(record.quantity, locale: locale)} ${record.unit} · ${formatDate(record.activityDate, locale: locale)}',
                  textDirection: TextDirection.ltr,
                  style: const TextStyle(fontSize: 10.5, color: AppColors.muted),
                ),
                if (record.notes.isNotEmpty) ...[
                  const SizedBox(height: 4),
                  Text(
                    record.notes,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(fontSize: 10, color: AppColors.muted),
                  ),
                ],
              ],
            ),
          ),
          const SizedBox(width: 8),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                formatKg(record.emissionsKg, locale: locale),
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
              ),
              Text(
                l10n.t('kgCo2e'),
                style: const TextStyle(fontSize: 9, color: AppColors.muted),
              ),
            ],
          ),
          const SizedBox(width: 2),
          const Icon(Icons.chevron_right_rounded, size: 18, color: AppColors.muted),
        ],
      ),
    );
  }
}
