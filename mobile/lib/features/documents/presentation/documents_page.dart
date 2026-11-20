import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import 'package:path/path.dart' as p;

import '../../../core/async_cubit.dart';
import '../../../core/format.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/models.dart';
import '../../../core/network/api_exception.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../dashboard/data/carbon_repository.dart';

class DocumentsPage extends StatefulWidget {
  const DocumentsPage({super.key});

  @override
  State<DocumentsPage> createState() => _DocumentsPageState();
}

class _DocumentsPageState extends State<DocumentsPage> {
  late AsyncCubit<List<Map<String, dynamic>>> _cubit;
  bool _uploading = false;

  Future<List<Map<String, dynamic>>> _load() =>
      context.read<CarbonRepository>().documents();

  @override
  void initState() {
    super.initState();
    _cubit = AsyncCubit<List<Map<String, dynamic>>>(const AsyncState())..run(_load);
  }

  @override
  void dispose() {
    _cubit.close();
    super.dispose();
  }

  Future<void> _pickAndUpload() async {
    final picker = ImagePicker();
    final file = await picker.pickImage(source: ImageSource.gallery, imageQuality: 88);
    if (file == null || !mounted) return;
    final consent = await _askConsent();
    if (consent == null || !mounted) return;
    setState(() => _uploading = true);
    try {
      final bytes = await file.readAsBytes();
      await context.read<CarbonRepository>().uploadDocument(
            bytes: bytes,
            filename: p.basename(file.name.isEmpty ? 'bill.jpg' : file.name),
            consent: consent,
          );
      if (!mounted) return;
      showSnack(context, context.tr('saved'));
      _cubit.run(_load, silent: true);
    } catch (error) {
      if (!mounted) return;
      showSnack(context, _friendly(error), error: true);
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  Future<bool?> _askConsent() async {
    var value = true;
    return showDialog<bool>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setDialogState) => AlertDialog(
          title: Text(context.tr('uploadBill')),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              CheckboxListTile(
                contentPadding: EdgeInsets.zero,
                value: value,
                activeColor: AppColors.forest,
                title: Text(
                  context.tr('consent'),
                  style: const TextStyle(fontSize: 11.5, height: 1.4),
                ),
                onChanged: (next) => setDialogState(() => value = next ?? false),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text(context.tr('cancel')),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(context, value),
              child: Text(context.tr('upload')),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _openDocument(Map<String, dynamic> document) async {
    final id = ni(document['id']);
    final consent = document['ai_consent'] == true;
    final action = await showModalBottomSheet<String>(
      context: context,
      showDragHandle: true,
      builder: (context) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 0, 20, 18),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(
                s(document['original_filename']),
                style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w800),
              ),
              const SizedBox(height: 4),
              Text(
                '${context.l10n.documentStatus(s(document['status']))} · ${formatBytes(ni(document['size_bytes']))}',
                style: const TextStyle(fontSize: 10, color: AppColors.muted),
              ),
              const SizedBox(height: 18),
              if (consent && document['record_id'] == null)
                FilledButton.icon(
                  onPressed: () => Navigator.pop(context, 'extract'),
                  icon: const Icon(Icons.auto_awesome_rounded, size: 18),
                  label: Text(context.tr('extracting').replaceAll('…', '')),
                ),
              if (document['record_id'] == null) ...[
                const SizedBox(height: 8),
                OutlinedButton.icon(
                  onPressed: () => Navigator.pop(context, 'manual'),
                  icon: const Icon(Icons.edit_outlined, size: 18),
                  label: Text(context.tr('manualEntry')),
                ),
              ],
              if (document['record_id'] != null) ...[
                const SizedBox(height: 10),
                Pill(
                  label:
                      '${context.tr('linkedRecord')} #${document['record_id']}',
                  color: AppColors.mint,
                  foreground: AppColors.forest,
                  icon: Icons.link_rounded,
                ),
              ],
              const SizedBox(height: 8),
              TextButton(
                onPressed: () => Navigator.pop(context, 'delete'),
                child: Text(
                  context.tr('delete'),
                  style: const TextStyle(color: AppColors.danger),
                ),
              ),
            ],
          ),
        ),
      ),
    );
    if (!mounted || action == null) return;
    if (action == 'delete') {
      await _delete(id);
    } else if (action == 'manual') {
      await _confirm(id, null);
    } else if (action == 'extract') {
      await _extract(id);
    }
  }

  Future<void> _extract(int id) async {
    setState(() => _uploading = true);
    try {
      final data = await context.read<CarbonRepository>().extractDocument(id);
      if (!mounted) return;
      final fields = map(data['fields']);
      await _confirm(id, fields);
      _cubit.run(_load, silent: true);
    } on ApiException catch (error) {
      if (!mounted) return;
      showSnack(
        context,
        '${error.message}\n${context.tr('extractionUnavailable')}',
        error: true,
      );
      final fields = error.details['fields'];
      await _confirm(id, fields is Map ? map(fields) : null);
    } catch (error) {
      if (!mounted) return;
      showSnack(context, _friendly(error), error: true);
    } finally {
      if (mounted) setState(() => _uploading = false);
    }
  }

  Future<void> _confirm(int id, Map<String, dynamic>? fields) async {
    if (!mounted) return;
    await showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      showDragHandle: true,
      builder: (context) => Padding(
        padding: EdgeInsets.only(bottom: MediaQuery.viewInsetsOf(context).bottom),
        child: _DocumentConfirmSheet(
          documentId: id,
          fields: fields,
          onSaved: () => _cubit.run(_load, silent: true),
        ),
      ),
    );
  }

  Future<void> _delete(int id) async {
    try {
      await context.read<CarbonRepository>().deleteDocument(id);
      if (!mounted) return;
      _cubit.run(_load, silent: true);
    } catch (error) {
      if (!mounted) return;
      showSnack(context, _friendly(error), error: true);
    }
  }

  String _friendly(Object error) => error is ApiException ? error.message : error.toString();

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
              l10n.t('documentsTitle'),
              style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
            ),
            const SizedBox(height: 2),
            Text(
              l10n.t('documentsSubtitle'),
              style: const TextStyle(fontSize: 11.5, color: AppColors.muted),
            ),
          ],
        ),
        actions: [
          IconButton(
            onPressed: _uploading ? null : _pickAndUpload,
            icon: _uploading
                ? const SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  )
                : const Icon(Icons.upload_file_rounded),
          ),
          const SizedBox(width: 8),
        ],
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: AsyncPageBody<List<Map<String, dynamic>>>(
          onRetry: () => _cubit.run(_load),
          builder: (documents) {
            if (documents.isEmpty) {
              return EmptyState(
                message: l10n.t('documentsSubtitle'),
                icon: Icons.upload_file_outlined,
                actionLabel: l10n.t('uploadBill'),
                onAction: _pickAndUpload,
              );
            }
            return ListView.separated(
              padding: const EdgeInsets.fromLTRB(20, 8, 20, 30),
              itemCount: documents.length,
              separatorBuilder: (_, _) => const SizedBox(height: 9),
              itemBuilder: (context, index) {
                final doc = documents[index];
                return CarbonCard(
                  onTap: () => _openDocument(doc),
                  padding: const EdgeInsets.all(14),
                  child: Row(
                    children: [
                      Container(
                        width: 40,
                        height: 40,
                        decoration: const BoxDecoration(
                          color: AppColors.mint,
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          s(doc['mime_type']).contains('pdf')
                              ? Icons.picture_as_pdf_outlined
                              : Icons.image_outlined,
                          color: AppColors.forest,
                          size: 19,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              s(doc['original_filename']),
                              maxLines: 1,
                              overflow: TextOverflow.ellipsis,
                              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600),
                            ),
                            const SizedBox(height: 3),
                            Text(
                              '${formatBytes(ni(doc['size_bytes']))} · ${formatDate(DateTime.tryParse(s(doc['created_at'])), locale: l10n.locale.languageCode)}',
                              style: const TextStyle(fontSize: 9.5, color: AppColors.muted),
                            ),
                          ],
                        ),
                      ),
                      Pill(
                        label: l10n.documentStatus(s(doc['status'])),
                        color: s(doc['status']) == 'confirmed'
                            ? AppColors.mint
                            : AppColors.cream,
                        foreground: AppColors.forest,
                      ),
                    ],
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }
}

String formatBytes(int bytes) {
  if (bytes < 1024) return '$bytes B';
  if (bytes < 1024 * 1024) return '${(bytes / 1024).toStringAsFixed(0)} KB';
  return '${(bytes / (1024 * 1024)).toStringAsFixed(1)} MB';
}

class _DocumentConfirmSheet extends StatefulWidget {
  const _DocumentConfirmSheet({
    required this.documentId,
    required this.fields,
    required this.onSaved,
  });

  final int documentId;
  final Map<String, dynamic>? fields;
  final VoidCallback onSaved;

  @override
  State<_DocumentConfirmSheet> createState() => _DocumentConfirmSheetState();
}

class _DocumentConfirmSheetState extends State<_DocumentConfirmSheet> {
  final _formKey = GlobalKey<FormState>();
  final _quantity = TextEditingController();
  final _vendor = TextEditingController();
  final _date = TextEditingController();
  List<Category> _categories = const [];
  List<Factor> _factors = const [];
  int? _categoryId;
  int? _factorId;
  DateTime _selectedDate = DateTime(2026, 6, 30);
  bool _loading = true;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    final fields = widget.fields;
    if (fields != null) {
      _quantity.text = fields['consumption_value']?.toString() ?? '';
      _vendor.text = s(fields['vendor']);
      final date = DateTime.tryParse('${s(fields['billing_period'])}-01');
      if (date != null) _selectedDate = date;
    }
    _date.text = DateFormat('yyyy-MM-dd').format(_selectedDate);
    _bootstrap();
  }

  Future<void> _bootstrap() async {
    try {
      final repo = context.read<CarbonRepository>();
      final categories = await repo.categories();
      if (!mounted) return;
      setState(() {
        _categories = categories;
        _categoryId = categories.isEmpty ? null : categories.first.id;
        _loading = false;
      });
      if (_categoryId != null) await _loadFactors(_categoryId!);
    } catch (_) {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _loadFactors(int categoryId) async {
    final factors = await context.read<CarbonRepository>().factors(categoryId: categoryId);
    if (!mounted) return;
    setState(() {
      _factors = factors;
      _factorId = factors.isEmpty ? null : factors.first.id;
    });
  }

  Factor? get _factor {
    for (final f in _factors) {
      if (f.id == _factorId) return f;
    }
    return null;
  }

  Future<void> _save() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    final factor = _factor;
    if (_categoryId == null || factor == null) return;
    setState(() => _saving = true);
    try {
      await context.read<CarbonRepository>().confirmDocument(
            widget.documentId,
            categoryId: _categoryId!,
            factorId: factor.id,
            quantity: double.parse(_quantity.text.trim()),
            unit: factor.unit,
            activityDate: DateFormat('yyyy-MM-dd').format(_selectedDate),
            vendor: _vendor.text.trim(),
          );
      if (!mounted) return;
      widget.onSaved();
      Navigator.pop(context);
      showSnack(context, context.tr('recordSaved'));
    } catch (error) {
      if (!mounted) return;
      setState(() => _saving = false);
      showSnack(context, error.toString(), error: true);
    }
  }

  @override
  void dispose() {
    _quantity.dispose();
    _vendor.dispose();
    _date.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 0, 20, 20),
      child: _loading
          ? const SizedBox(
              height: 180,
              child: Center(child: CircularProgressIndicator()),
            )
          : Form(
              key: _formKey,
              child: ListView(
                shrinkWrap: true,
                children: [
                  Text(
                    l10n.t('confirmValues'),
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    widget.fields == null
                        ? l10n.t('manualEntry')
                        : 'AI · ${l10n.t('bestEffort')}',
                    style: const TextStyle(fontSize: 10, color: AppColors.muted),
                  ),
                  const SizedBox(height: 16),
                  Text(l10n.t('category'), style: _labelStyle),
                  const SizedBox(height: 7),
                  DropdownButtonFormField<int>(
                    initialValue: _categoryId,
                    isExpanded: true,
                    items: [
                      for (final category in _categories)
                        DropdownMenuItem(
                          value: category.id,
                          child: Text(category.name(l10n.locale.languageCode)),
                        ),
                    ],
                    onChanged: (value) {
                      if (value == null) return;
                      setState(() {
                        _categoryId = value;
                        _factors = const [];
                        _factorId = null;
                      });
                      _loadFactors(value);
                    },
                  ),
                  const SizedBox(height: 12),
                  Text(l10n.t('factor'), style: _labelStyle),
                  const SizedBox(height: 7),
                  DropdownButtonFormField<int>(
                    key: ValueKey('doc-factor-$_categoryId-$_factorId'),
                    initialValue: _factorId,
                    isExpanded: true,
                    items: [
                      for (final factor in _factors)
                        DropdownMenuItem(
                          value: factor.id,
                          child: Text(
                            factor.name(l10n.locale.languageCode),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                    ],
                    onChanged: (value) => setState(() => _factorId = value),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(l10n.t('quantity'), style: _labelStyle),
                            const SizedBox(height: 7),
                            TextFormField(
                              controller: _quantity,
                              keyboardType:
                                  const TextInputType.numberWithOptions(decimal: true),
                              decoration: InputDecoration(suffixText: _factor?.unit ?? ''),
                              validator: (value) {
                                final parsed = double.tryParse((value ?? '').trim());
                                return parsed == null || parsed <= 0
                                    ? l10n.t('validationError')
                                    : null;
                              },
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(l10n.t('activityDate'), style: _labelStyle),
                            const SizedBox(height: 7),
                            TextFormField(
                              controller: _date,
                              readOnly: true,
                              onTap: () async {
                                final picked = await showDatePicker(
                                  context: context,
                                  initialDate: _selectedDate,
                                  firstDate: DateTime(2020),
                                  lastDate: DateTime(2032),
                                );
                                if (picked == null) return;
                                setState(() {
                                  _selectedDate = picked;
                                  _date.text = DateFormat('yyyy-MM-dd').format(picked);
                                });
                              },
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Text(l10n.t('vendor'), style: _labelStyle),
                  const SizedBox(height: 7),
                  TextFormField(controller: _vendor),
                  const SizedBox(height: 16),
                  FilledButton(
                    onPressed: _saving ? null : _save,
                    child: _saving
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : Text(l10n.t('confirmValues')),
                  ),
                ],
              ),
            ),
    );
  }

  TextStyle get _labelStyle => const TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.w700,
        color: AppColors.ink,
      );
}
