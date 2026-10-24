import 'package:flutter_test/flutter_test.dart';
import 'package:issue_9_flutter_chart_reference/main.dart';

void main() {
  testWidgets('loads shared synthetic fixture and exposes data table', (tester) async {
    await tester.pumpWidget(const Issue9ChartApp());
    await tester.pumpAndSettle();
    expect(find.text('Market chart reference PoC'), findsOneWidget);
    expect(find.textContaining('Synthetic test data only.'), findsOneWidget);
    expect(find.textContaining('2026-01-05T00:00:00Z'), findsWidgets);
    expect(find.byType(DataTable), findsOneWidget);
  });
}
