import 'package:intl/intl.dart';

String formatKg(num kg, {String? locale}) {
  final value = kg.toDouble();
  if (value.abs() >= 1000) {
    return NumberFormat('#,##0', locale).format(value);
  }
  if (value.abs() >= 10) {
    return NumberFormat('#,##0.0', locale).format(value);
  }
  return NumberFormat('#,##0.00', locale).format(value);
}

String formatNumber(num value, {String? locale, int? decimals}) {
  final pattern = decimals == null ? '#,##0.##' : '#,##0.${'0' * decimals}';
  return NumberFormat(pattern, locale).format(value);
}

String formatPercent(num value, {String? locale}) =>
    '${NumberFormat('#,##0.0', locale).format(value)}%';

DateTime? parseApiDate(String? raw) => raw == null ? null : DateTime.tryParse(raw);

String formatDate(DateTime? date, {String locale = 'en', String pattern = 'd MMM y'}) {
  if (date == null) return '—';
  return DateFormat(pattern, locale).format(date);
}

String formatDateTime(DateTime? date, {String locale = 'en'}) {
  if (date == null) return '—';
  return DateFormat('d MMM · HH:mm', locale).format(date.toLocal());
}

String greetingKeyFor(DateTime now) {
  if (now.hour < 12) return 'greetingMorning';
  if (now.hour < 17) return 'greetingAfternoon';
  return 'greetingEvening';
}
