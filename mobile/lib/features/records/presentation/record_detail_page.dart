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

class RecordDetailPage extends StatefulWidget {
  const RecordDetailPage({super.key, required this.recordId});

  final int recordId;

  @override
  State<RecordDetailPage> createState() => _RecordDetailPageState();
}

class _RecordDetailPageState extends State<RecordDetailPage> {
  late AsyncCubit<ActivityRecord> _cubit;

  @override
  void initState() {
    super.initState();
    _cubit = AsyncCubit<ActivityRecord>(const AsyncState())
      ..run(() => context.read<CarbonRepository>().record(widget.recordId));
  }

  Future<void> _delete() async {
    final l10n = context.l10n;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(l10n.t('deleteRecord')),
        content: Text(l10n.t('deleteConfirm')),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: Text(l10n.t('cancel'))),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: AppColors.danger),
            onPressed: () => Navigator.pop(context, true),
            child: Text(l10n.t('delete')),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    try {
      await context.read<CarbonRepository>().deleteRecord(widget.recordId);
      if (!mounted) return;
      showSnack(context, l10n.t('recordDeleted'));
      context.pop(true);
    } catch (error) {
      if (!mounted) return;
      showSnack(context, error.toString(), error: true);
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
        title: Text(
          l10n.t('recordsTitle'),
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
        actions: [
          IconButton(
            onPressed: _delete,
            icon: const Icon(Icons.delete_outline_rounded),
          ),
        ],
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: AsyncPageBody<ActivityRecord>(
          onRetry: () => _cubit.run(
            () => context.read<CarbonRepository>().record(widget.recordId),
          ),
          builder: (record) => _RecordDetail(
            record: record,
            onChanged: () => _cubit.run(
              () => context.read<CarbonRepository>().record(widget.recordId),
            ),
          ),
        ),
      ),
    );
  }
}

class _RecordDetail extends StatelessWidget {
  const _RecordDetail({required this.record, required this.onChanged});

  final ActivityRecord record;
  final VoidCallback onChanged;

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final locale = l10n.locale.languageCode;
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
      children: [
        Container(
          padding: const EdgeInsets.all(22),
          decoration: BoxDecoration(
            gradient: const LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [AppColors.forestDeep, AppColors.forest],
            ),
            borderRadius: BorderRadius.circular(26),
          ),
          child: Column(
            children: [
              CategoryAvatar(category: record.category, size: 54),
              const SizedBox(height: 14),
              Text(
                record.category?.name(locale) ?? '—',
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.7),
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                '${formatKg(record.emissionsKg, locale: locale)} kg CO₂e',
                textDirection: TextDirection.ltr,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 34,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -1,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                formatDate(record.activityDate, locale: locale),
                style: TextStyle(
                  color: Colors.white.withValues(alpha: 0.55),
                  fontSize: 11,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        CarbonCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  const Icon(Icons.receipt_long_outlined, size: 18, color: AppColors.forest),
                  const SizedBox(width: 8),
                  Text(
                    l10n.t('formula'),
                    style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700),
                  ),
                  const Spacer(),
                  Pill(label: record.source == 'document' ? l10n.t('document') : l10n.t('manualEntry')),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                record.formula,
                textDirection: TextDirection.ltr,
                style: const TextStyle(fontSize: 12, height: 1.55, color: AppColors.ink),
              ),
              const Divider(height: 28),
              DetailRow(
                label: l10n.t('factor'),
                value: record.factor?.name(locale) ?? '—',
              ),
              DetailRow(
                label: l10n.t('quantity'),
                value: '${formatNumber(record.quantity)} ${record.unit}',
                ltr: true,
              ),
              DetailRow(
                label: l10n.t('factorSource'),
                value: record.factorSource,
              ),
              DetailRow(
                label: l10n.t('factor'),
                value: '${formatNumber(record.factorGrams)} g CO₂e / ${record.unit}',
                ltr: true,
              ),
            ],
          ),
        ),
        if (record.notes.isNotEmpty) ...[
          const SizedBox(height: 14),
          CarbonCard(
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.notes_rounded, size: 18, color: AppColors.muted),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    record.notes,
                    style: const TextStyle(fontSize: 12, height: 1.5),
                  ),
                ),
              ],
            ),
          ),
        ],
        const SizedBox(height: 14),
        Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: AppColors.mint,
            borderRadius: BorderRadius.circular(16),
          ),
          child: Row(
            children: [
              const Icon(Icons.shield_outlined, size: 17, color: AppColors.forest),
              const SizedBox(width: 9),
              Expanded(
                child: Text(
                  l10n.t('calculated'),
                  style: const TextStyle(fontSize: 10.5, color: AppColors.forest),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        OutlinedButton.icon(
          onPressed: () async {
            await context.push('/records/${record.id}/edit');
            onChanged();
          },
          icon: const Icon(Icons.edit_outlined, size: 18),
          label: Text(l10n.t('editRecord')),
        ),
      ],
    );
  }
}
