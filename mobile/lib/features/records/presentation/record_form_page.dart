import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';

import '../../../core/config/app_config.dart';
import '../../../core/format.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/models.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../dashboard/data/carbon_repository.dart';

class RecordFormPage extends StatefulWidget {
  const RecordFormPage({super.key, this.recordId});

  final int? recordId;

  @override
  State<RecordFormPage> createState() => _RecordFormPageState();
}

class _RecordFormPageState extends State<RecordFormPage> {
  final _formKey = GlobalKey<FormState>();
  final _quantity = TextEditingController();
  final _notes = TextEditingController();
  final _dateController = TextEditingController();

  List<Category> _categories = const [];
  List<Factor> _factors = const [];
  int? _categoryId;
  int? _factorId;
  DateTime _date = AppConfig.demoToday;
  bool _loading = true;
  bool _loadingFactors = false;
  bool _saving = false;
  String? _loadError;
  ActivityRecord? _existing;

  @override
  void initState() {
    super.initState();
    _dateController.text = DateFormat('yyyy-MM-dd').format(_date);
    _bootstrap();
  }

  @override
  void dispose() {
    _quantity.dispose();
    _notes.dispose();
    _dateController.dispose();
    super.dispose();
  }

  Future<void> _bootstrap() async {
    try {
      final repo = context.read<CarbonRepository>();
      final categories = await repo.categories(force: true);
      ActivityRecord? existing;
      if (widget.recordId != null) {
        existing = await repo.record(widget.recordId!);
      }
      if (!mounted) return;
      setState(() {
        _categories = categories;
        _existing = existing;
        if (existing != null) {
          _categoryId = existing.category?.id ?? existing.factor?.categoryId;
          _factorId = existing.factor?.id;
          _quantity.text = formatNumber(existing.quantity);
          _notes.text = existing.notes;
          _date = existing.activityDate ?? AppConfig.demoToday;
          _dateController.text = DateFormat('yyyy-MM-dd').format(_date);
        } else if (categories.isNotEmpty) {
          _categoryId = categories.first.id;
        }
        _loading = false;
      });
      if (_categoryId != null) await _loadFactors(_categoryId!, keepFactor: true);
    } catch (error) {
      if (!mounted) return;
      setState(() {
        _loading = false;
        _loadError = error.toString();
      });
    }
  }

  Future<void> _loadFactors(int categoryId, {bool keepFactor = false}) async {
    setState(() => _loadingFactors = true);
    try {
      final factors = await context.read<CarbonRepository>().factors(
            categoryId: categoryId,
            force: true,
          );
      if (!mounted) return;
      setState(() {
        _factors = factors;
        _loadingFactors = false;
        if (!keepFactor || !factors.any((f) => f.id == _factorId)) {
          _factorId = factors.isEmpty ? null : factors.first.id;
        }
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _factors = const [];
        _factorId = null;
        _loadingFactors = false;
      });
    }
  }

  Factor? get _selectedFactor {
    for (final factor in _factors) {
      if (factor.id == _factorId) return factor;
    }
    return null;
  }

  double get _previewKg {
    final qty = double.tryParse(_quantity.text) ?? 0;
    final factor = _selectedFactor;
    if (factor == null || qty <= 0) return 0;
    return qty * factor.factorGrams / 1000;
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _date,
      firstDate: DateTime(2020),
      lastDate: DateTime(2032),
      builder: (context, child) => Theme(
        data: Theme.of(context).copyWith(
          colorScheme: Theme.of(context).colorScheme.copyWith(primary: AppColors.forest),
        ),
        child: child!,
      ),
    );
    if (picked != null) {
      setState(() {
        _date = picked;
        _dateController.text = DateFormat('yyyy-MM-dd').format(picked);
      });
    }
  }

  Future<void> _save() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final factor = _selectedFactor;
    if (_categoryId == null || factor == null) return;
    setState(() => _saving = true);
    final body = {
      'category_id': _categoryId,
      'factor_id': factor.id,
      'activity_date': DateFormat('yyyy-MM-dd').format(_date),
      'quantity': double.parse(_quantity.text.trim()),
      'unit': factor.unit,
      if (_notes.text.trim().isNotEmpty) 'notes': _notes.text.trim(),
    };
    try {
      final repo = context.read<CarbonRepository>();
      if (_existing == null) {
        await repo.createRecord(body);
      } else {
        await repo.updateRecord(_existing!.id, body);
      }
      if (!mounted) return;
      showSnack(context, context.tr('recordSaved'));
      context.pop(true);
    } catch (error) {
      if (!mounted) return;
      setState(() => _saving = false);
      showSnack(context, _friendly(error), error: true);
    }
  }

  String _friendly(Object error) {
    final raw = error.toString();
    if (raw.startsWith('ApiException')) {
      final index = raw.indexOf('): ');
      if (index > -1) return raw.substring(index + 3);
    }
    return raw;
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    final locale = l10n.locale.languageCode;
    return Scaffold(
      appBar: AppBar(
        title: Text(
          l10n.t(_existing == null ? 'newRecord' : 'editRecord'),
          style: const TextStyle(fontWeight: FontWeight.w800),
        ),
      ),
      body: _loading
          ? const LoadingList(itemCount: 2)
          : _loadError != null
              ? ErrorState(message: _loadError, onRetry: _bootstrap)
              : Form(
                  key: _formKey,
                  child: ListView(
                    padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
                    children: [
                      Text(l10n.t('category'), style: _labelStyle),
                      const SizedBox(height: 8),
                      Wrap(
                        spacing: 8,
                        runSpacing: 8,
                        children: [
                          for (final category in _categories)
                            ChoiceChip(
                              label: Text(category.name(locale)),
                              avatar: Icon(
                                CategoryAvatar.iconFor(category.key),
                                size: 15,
                              ),
                              selected: _categoryId == category.id,
                              showCheckmark: false,
                              onSelected: (_) {
                                setState(() {
                                  _categoryId = category.id;
                                  _factors = const [];
                                  _factorId = null;
                                });
                                _loadFactors(category.id);
                              },
                            ),
                        ],
                      ),
                      const SizedBox(height: 20),
                      Text(l10n.t('factor'), style: _labelStyle),
                      const SizedBox(height: 8),
                      if (_loadingFactors)
                        const Padding(
                          padding: EdgeInsets.all(18),
                          child: Center(
                            child: SizedBox(
                              width: 22,
                              height: 22,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                          ),
                        )
                      else if (_factors.isEmpty)
                        CarbonCard(
                          child: Text(
                            l10n.t('noData'),
                            style: const TextStyle(color: AppColors.muted),
                          ),
                        )
                      else
                        DropdownButtonFormField<int>(
                          initialValue: _factorId,
                          isExpanded: true,
                          decoration: const InputDecoration(
                            prefixIcon: Icon(Icons.science_outlined, size: 20),
                          ),
                          items: [
                            for (final factor in _factors)
                              DropdownMenuItem(
                                value: factor.id,
                                child: Row(
                                  children: [
                                    Flexible(
                                      child: BidiText(
                                        factor.name(locale),
                                        maxLines: 1,
                                        overflow: TextOverflow.ellipsis,
                                        style: const TextStyle(fontSize: 12.5),
                                      ),
                                    ),
                                    const SizedBox(width: 8),
                                    Text(
                                      '${formatNumber(factor.factorGrams)} g / ${factor.unit}',
                                      textDirection: ui.TextDirection.ltr,
                                      style: const TextStyle(
                                        fontSize: 10,
                                        color: AppColors.muted,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                          ],
                          onChanged: (value) => setState(() => _factorId = value),
                        ),
                      if (_selectedFactor != null) ...[
                        const SizedBox(height: 9),
                        Container(
                          padding: const EdgeInsets.all(12),
                          decoration: BoxDecoration(
                            color: AppColors.mint,
                            borderRadius: BorderRadius.circular(14),
                          ),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              const Icon(
                                Icons.verified_outlined,
                                size: 16,
                                color: AppColors.forest,
                              ),
                              const SizedBox(width: 8),
                              Expanded(
                                child: BidiText(
                                  '${l10n.t('factorSource')}: ${_selectedFactor!.sourceLabel}',
                                  style: const TextStyle(
                                    fontSize: 10,
                                    color: AppColors.forest,
                                    height: 1.4,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                      const SizedBox(height: 20),
                      Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Expanded(
                            flex: 1,
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(l10n.t('quantity'), style: _labelStyle),
                                const SizedBox(height: 8),
                                Directionality(
                                  textDirection: ui.TextDirection.ltr,
                                  child: TextFormField(
                                    controller: _quantity,
                                    keyboardType: const TextInputType.numberWithOptions(
                                      decimal: true,
                                    ),
                                    textAlign: TextAlign.left,
                                    onChanged: (_) => setState(() {}),
                                    decoration: InputDecoration(
                                      hintText: '0',
                                      suffixText: _selectedFactor?.unit ?? '',
                                    ),
                                    validator: (value) {
                                      final parsed = double.tryParse((value ?? '').trim());
                                      if (parsed == null || parsed <= 0) {
                                        return l10n.t('validationError');
                                      }
                                      return null;
                                    },
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 10),
                          Expanded(
                            flex: 1,
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(l10n.t('activityDate'), style: _labelStyle),
                                const SizedBox(height: 8),
                                TextFormField(
                                  controller: _dateController,
                                  readOnly: true,
                                  onTap: _pickDate,
                                  textAlign: TextAlign.left,
                                  textDirection: ui.TextDirection.ltr,
                                  style: const TextStyle(fontSize: 12.5),
                                  decoration: const InputDecoration(
                                    suffixIconConstraints: BoxConstraints(minWidth: 30),
                                    suffixIcon: Icon(Icons.calendar_today_outlined, size: 16),
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 20),
                      Text(l10n.t('notes'), style: _labelStyle),
                      const SizedBox(height: 8),
                      TextFormField(
                        controller: _notes,
                        maxLines: 3,
                        maxLength: 1000,
                        decoration: const InputDecoration(
                          hintText: 'Optional context',
                          counterText: '',
                        ),
                      ),
                      const SizedBox(height: 14),
                      Container(
                        padding: const EdgeInsets.all(16),
                        decoration: BoxDecoration(
                          color: AppColors.forestDeep,
                          borderRadius: BorderRadius.circular(18),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.calculate_outlined, color: AppColors.sandSoft, size: 20),
                            const SizedBox(width: 10),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    l10n.t('formula'),
                                    style: TextStyle(
                                      color: Colors.white.withValues(alpha: 0.6),
                                      fontSize: 10,
                                    ),
                                  ),
                                  const SizedBox(height: 3),
                                  Text(
                                    _selectedFactor == null
                                        ? '—'
                                        : '${formatNumber(double.tryParse(_quantity.text) ?? 0)} × '
                                            '${formatNumber(_selectedFactor!.factorGrams)} g = '
                                            '${formatKg(_previewKg, locale: locale)} kg',
                                    textDirection: ui.TextDirection.ltr,
                                    style: const TextStyle(
                                      color: Colors.white,
                                      fontSize: 12,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                            Text(
                              '${formatKg(_previewKg, locale: locale)} kg',
                              textDirection: ui.TextDirection.ltr,
                              style: const TextStyle(
                                color: Colors.white,
                                fontSize: 16,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(height: 10),
                      Text(
                        l10n.t('calculated'),
                        style: const TextStyle(fontSize: 9.5, color: AppColors.muted),
                      ),
                      const SizedBox(height: 20),
                      FilledButton(
                        onPressed: _saving ? null : _save,
                        child: _saving
                            ? const SizedBox(
                                width: 20,
                                height: 20,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: Colors.white,
                                ),
                              )
                            : Text(l10n.t('saveChanges')),
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
