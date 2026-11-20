import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';

import '../../../core/async_cubit.dart';
import '../../../core/localization/app_localizations.dart';
import '../../../core/models.dart';
import '../../../core/theme/app_theme.dart';
import '../../../core/widgets/app_widgets.dart';
import '../../dashboard/data/carbon_repository.dart';

class OrganizationPage extends StatefulWidget {
  const OrganizationPage({super.key});

  @override
  State<OrganizationPage> createState() => _OrganizationPageState();
}

class _OrganizationPageState extends State<OrganizationPage> {
  late AsyncCubit<Map<String, dynamic>> _cubit;

  Future<Map<String, dynamic>> _load() =>
      context.read<CarbonRepository>().organization();

  @override
  void initState() {
    super.initState();
    _cubit = AsyncCubit<Map<String, dynamic>>(const AsyncState())..run(_load);
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
          l10n.t('orgTitle'),
          style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
        ),
      ),
      body: BlocProvider.value(
        value: _cubit,
        child: AsyncPageBody<Map<String, dynamic>>(
          onRetry: () => _cubit.run(_load),
          builder: (org) => _OrganizationForm(
            organization: org,
            onSaved: () => _cubit.run(_load, silent: true),
          ),
        ),
      ),
    );
  }
}

class _OrganizationForm extends StatefulWidget {
  const _OrganizationForm({required this.organization, required this.onSaved});

  final Map<String, dynamic> organization;
  final VoidCallback onSaved;

  @override
  State<_OrganizationForm> createState() => _OrganizationFormState();
}

class _OrganizationFormState extends State<_OrganizationForm> {
  late final TextEditingController _nameEn;
  late final TextEditingController _nameAr;
  late final TextEditingController _industry;
  late final TextEditingController _country;
  late final TextEditingController _city;
  late final TextEditingController _contact;
  String? _type;
  String? _size;
  bool _saving = false;

  @override
  void initState() {
    super.initState();
    final org = widget.organization;
    _nameEn = TextEditingController(text: s(org['name_en']));
    _nameAr = TextEditingController(text: s(org['name_ar']));
    _industry = TextEditingController(text: s(org['industry']));
    _country = TextEditingController(text: s(org['country']));
    _city = TextEditingController(text: s(org['city']));
    _contact = TextEditingController(text: s(org['contact_email']));
    _type = s(org['org_type']).isEmpty ? null : s(org['org_type']);
    _size = s(org['size']).isEmpty ? null : s(org['size']);
  }

  @override
  void dispose() {
    _nameEn.dispose();
    _nameAr.dispose();
    _industry.dispose();
    _country.dispose();
    _city.dispose();
    _contact.dispose();
    super.dispose();
  }

  Future<void> _save() async {
    if (_nameEn.text.trim().length < 2) {
      showSnack(context, context.tr('validationError'), error: true);
      return;
    }
    setState(() => _saving = true);
    try {
      await context.read<CarbonRepository>().updateOrganization({
        'name_en': _nameEn.text.trim(),
        'name_ar': _nameAr.text.trim(),
        if (_type != null) 'org_type': _type,
        'industry': _industry.text.trim(),
        'country': _country.text.trim(),
        'city': _city.text.trim(),
        if (_size != null) 'size': _size,
        if (_contact.text.trim().isNotEmpty) 'contact_email': _contact.text.trim(),
      });
      if (!mounted) return;
      showSnack(context, context.tr('saved'));
      widget.onSaved();
    } catch (error) {
      if (!mounted) return;
      showSnack(context, error.toString(), error: true);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = context.l10n;
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 8, 20, 32),
      children: [
        CarbonCard(
          color: AppColors.forestDeep,
          child: Row(
            children: [
              Container(
                width: 46,
                height: 46,
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(14),
                ),
                child: const Icon(Icons.business_rounded, color: Colors.white, size: 23),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  _nameEn.text.isEmpty ? l10n.t('organizationProfile') : _nameEn.text,
                  style: const TextStyle(
                    color: Colors.white,
                    fontSize: 15,
                    fontWeight: FontWeight.w800,
                  ),
                ),
              ),
              if (widget.organization['is_verified'] == true)
                Pill(
                  label: l10n.t('verifiedOrganization'),
                  color: AppColors.mint,
                  foreground: AppColors.forest,
                  icon: Icons.verified_rounded,
                ),
            ],
          ),
        ),
        const SizedBox(height: 20),
        Text(l10n.t('orgNameEn'), style: _labelStyle),
        const SizedBox(height: 7),
        TextFormField(controller: _nameEn),
        const SizedBox(height: 15),
        Text(l10n.t('orgNameAr'), style: _labelStyle),
        const SizedBox(height: 7),
        TextFormField(controller: _nameAr, textDirection: TextDirection.rtl),
        const SizedBox(height: 15),
        Text(l10n.t('industry'), style: _labelStyle),
        const SizedBox(height: 7),
        TextFormField(controller: _industry),
        const SizedBox(height: 15),
        Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(l10n.t('size'), style: _labelStyle),
                  const SizedBox(height: 7),
                  DropdownButtonFormField<String>(
                    initialValue: _size,
                    isExpanded: true,
                    items: [
                      for (final item in const ['1-10', '11-50', '51-200', '200+'])
                        DropdownMenuItem(value: item, child: Text(item)),
                    ],
                    onChanged: (value) => setState(() => _size = value),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(l10n.t('country'), style: _labelStyle),
                  const SizedBox(height: 7),
                  TextFormField(controller: _country),
                ],
              ),
            ),
          ],
        ),
        const SizedBox(height: 15),
        Text(l10n.t('city'), style: _labelStyle),
        const SizedBox(height: 7),
        TextFormField(controller: _city),
        const SizedBox(height: 15),
        Text(l10n.t('contactEmail'), style: _labelStyle),
        const SizedBox(height: 7),
        TextFormField(
          controller: _contact,
          keyboardType: TextInputType.emailAddress,
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
              : Text(l10n.t('updateOrg')),
        ),
      ],
    );
  }

  TextStyle get _labelStyle => const TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.w700,
        color: AppColors.ink,
      );
}
