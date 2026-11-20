import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/config/app_config.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../dashboard/data/carbon_repository.dart';

class GoalFormPage extends StatefulWidget {
  const GoalFormPage({super.key});

  @override
  State<GoalFormPage> createState() => _GoalFormPageState();
}

class _GoalFormPageState extends State<GoalFormPage> {
  final _formKey = GlobalKey<FormState>();
  final _title = TextEditingController();
  double _target = 20;
  String _periodType = 'monthly';
  late DateTime _start;
  late DateTime _end;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    _start = AppConfig.demoToday;
    _end = _start.add(const Duration(days: 90));
    final l10n = context.l10n;
    _title.text = l10n.isArabic ? 'تقليل بصمتي' : 'Reduce my footprint';
  }

  @override
  void dispose() {
    _title.dispose();
    super.dispose();
  }

  void _setPeriod(String value) {
    setState(() {
      _periodType = value;
      _end = _start.add(
        Duration(
          days: value == 'weekly'
              ? 7
              : value == 'yearly'
                  ? 365
                  : 90,
        ),
      );
    });
  }

  Future<void> _pickDate({required bool start}) async {
    final picked = await showDatePicker(
      context: context,
      initialDate: start ? _start : _end,
      firstDate: DateTime(2020),
      lastDate: DateTime(2035),
    );
    if (picked == null) return;
    setState(() {
      if (start) {
        _start = picked;
        if (_end.isBefore(_start)) _end = _start.add(const Duration(days: 30));
      } else {
        _end = picked;
      }
    });
  }

  Future<void> _save() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() => _saving = true);
    try {
      await context.read<CarbonRepository>().createGoal({
        'title': _title.text.trim(),
        'target_percent': _target,
        'period_type': _periodType,
        'start_date': DateFormat('yyyy-MM-dd').format(_start),
        'end_date': DateFormat('yyyy-MM-dd').format(_end),
      });
      if (!mounted) return;
      showSnack(context, context.tr('goalCreated'));
      context.pop(true);
    } catch (error) {
      if (!mounted) return;
      setState(() => _saving = false);
      showSnack(context, error.toString(), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return Scaffold(
      appBar: AppBar(
        title: Text(
          l10n.t('newGoal'),
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
          children: [
            Text(l10n.t('title'), style: _labelStyle),
            const SizedBox(height: 8),
            TextFormField(
              controller: _title,
              maxLength: 200,
              decoration: const InputDecoration(counterText: ''),
              validator: (value) =>
                  (value ?? '').trim().length < 2 ? l10n.t('validationError') : null,
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Text(l10n.t('targetPercent'), style: _labelStyle),
                const Spacer(),
                Text(
                  '${_target.round()}%',
                  style: const TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.w800,
                    color: AppColors.forest,
                  ),
                ),
              ],
            ),
            Slider(
              value: _target,
              min: 5,
              max: 60,
              divisions: 11,
              activeColor: AppColors.forest,
              label: '${_target.round()}%',
              onChanged: (value) => setState(() => _target = value),
            ),
            Text(
              l10n.isArabic
                  ? 'يُحسب خط الأساس تلقائيًا من السجلات السابقة.'
                  : 'The baseline is calculated automatically from your earlier records.',
              style: const TextStyle(fontSize: 11, color: AppColors.muted),
            ),
            const SizedBox(height: 20),
            Text(l10n.t('period'), style: _labelStyle),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              children: [
                for (final item in const [
                  ('weekly', 'week'),
                  ('monthly', 'month'),
                  ('yearly', 'year'),
                ])
                  ChoiceChip(
                    label: Text(l10n.t(item.$2)),
                    selected: _periodType == item.$1,
                    showCheckmark: false,
                    onSelected: (_) => _setPeriod(item.$1),
                  ),
              ],
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                Expanded(
                  child: _DateField(
                    label: l10n.t('startDate'),
                    date: _start,
                    onTap: () => _pickDate(start: true),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: _DateField(
                    label: l10n.t('endDate'),
                    date: _end,
                    onTap: () => _pickDate(start: false),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 22),
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: AppColors.mint,
                borderRadius: BorderRadius.circular(18),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.calculate_outlined, size: 18, color: AppColors.forest),
                  const SizedBox(width: 9),
                  Expanded(
                    child: Text(
                      l10n.isArabic
                          ? 'ينشئ الخادم هدفًا من خط أساسك المقاس. لا يستخدم الذكاء الاصطناعي لتوليد أرقام الانبعاثات.'
                          : 'The server creates the goal from your measured baseline. AI is never used to generate emission numbers.',
                      style: const TextStyle(fontSize: 10.5, height: 1.45, color: AppColors.forest),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),
            FilledButton(
              onPressed: _saving ? null : _save,
              child: _saving
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                    )
                  : Text(l10n.t('createGoal')),
            ),
          ],
        ),
      ),
    );
  }

  TextStyle get _labelStyle => const TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w700,
        color: AppColors.ink,
      );
}

class _DateField extends StatelessWidget {
  const _DateField({required this.label, required this.date, required this.onTap});

  final String label;
  final DateTime date;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
        ),
        const SizedBox(height: 7),
        InkWell(
          onTap: onTap,
          borderRadius: BorderRadius.circular(16),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
            decoration: BoxDecoration(
              color: AppColors.paper,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.line),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    DateFormat('d MMM y').format(date),
                    style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                  ),
                ),
                const Icon(Icons.calendar_today_outlined, size: 16, color: AppColors.muted),
              ],
            ),
          ),
        ),
      ],
    );
  }
}
