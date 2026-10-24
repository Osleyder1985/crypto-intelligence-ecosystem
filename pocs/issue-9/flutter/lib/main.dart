import 'dart:convert';
import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:flutter/services.dart' show rootBundle;

void main() => runApp(const Issue9ChartApp());

class Candle {
  const Candle({required this.timestamp, required this.open, required this.high, required this.low, required this.close, required this.volume});
  final String timestamp;
  final double open;
  final double high;
  final double low;
  final double close;
  final double volume;

  factory Candle.fromJson(Map<String, dynamic> json) => Candle(
    timestamp: json['timestamp'] as String,
    open: (json['open'] as num).toDouble(),
    high: (json['high'] as num).toDouble(),
    low: (json['low'] as num).toDouble(),
    close: (json['close'] as num).toDouble(),
    volume: (json['volume'] as num).toDouble(),
  );
}

class Issue9ChartApp extends StatelessWidget {
  const Issue9ChartApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'Issue 9 chart reference',
    theme: ThemeData(colorScheme: ColorScheme.fromSeed(seedColor: Colors.teal), useMaterial3: true),
    home: const ChartScreen(),
  );
}

class ChartScreen extends StatefulWidget {
  const ChartScreen({super.key});
  @override
  State<ChartScreen> createState() => _ChartScreenState();
}

class _ChartScreenState extends State<ChartScreen> {
  late final Future<List<Candle>> _candles = _loadCandles();

  Future<List<Candle>> _loadCandles() async {
    final text = await rootBundle.loadString('assets/ohlcv_synthetic_v1.json');
    final data = jsonDecode(text) as Map<String, dynamic>;
    if (data['kind'] != 'synthetic-not-market-data') throw const FormatException('Fixture provenance marker is missing');
    return (data['candles'] as List<dynamic>).map((item) => Candle.fromJson(item as Map<String, dynamic>)).toList(growable: false);
  }

  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: AppBar(title: const Text('Market chart reference PoC')),
    body: FutureBuilder<List<Candle>>(
      future: _candles,
      builder: (context, snapshot) {
        if (snapshot.hasError) return Center(child: Text('Fixture load failed: ${snapshot.error}'));
        if (!snapshot.hasData) return const Center(child: CircularProgressIndicator(semanticsLabel: 'Loading synthetic chart fixture'));
        final candles = snapshot.data!;
        return ListView(padding: const EdgeInsets.all(16), children: [
          const Text('Synthetic test data only. This screen is not market data and does not generate investment signals.'),
          const SizedBox(height: 12),
          Semantics(
            label: 'Candlestick and volume chart for ${candles.length} synthetic OHLCV candles. Pinch to zoom and drag to pan.',
            child: InteractiveViewer(
              minScale: 0.5,
              maxScale: 4.0,
              constrained: false,
              clipBehavior: Clip.hardEdge,
              child: SizedBox(width: 1000, height: 360, child: CustomPaint(painter: CandleChartPainter(candles))),
            ),
          ),
          const SizedBox(height: 12),
          Text('UTC range: ${candles.first.timestamp} — ${candles.last.timestamp}'),
          const SizedBox(height: 8),
          SingleChildScrollView(scrollDirection: Axis.horizontal, child: DataTable(
            columns: const [DataColumn(label: Text('UTC timestamp')), DataColumn(label: Text('Open')), DataColumn(label: Text('High')), DataColumn(label: Text('Low')), DataColumn(label: Text('Close')), DataColumn(label: Text('Volume'))],
            rows: candles.map((c) => DataRow(cells: [DataCell(Text(c.timestamp)), DataCell(Text('${c.open}')), DataCell(Text('${c.high}')), DataCell(Text('${c.low}')), DataCell(Text('${c.close}')), DataCell(Text('${c.volume}'))])).toList(growable: false),
          )),
        ]);
      },
    ),
  );
}

class CandleChartPainter extends CustomPainter {
  CandleChartPainter(this.candles);
  final List<Candle> candles;

  @override
  void paint(Canvas canvas, Size size) {
    if (candles.isEmpty || size.width <= 0 || size.height <= 0) return;
    const left = 30.0;
    const right = 12.0;
    const top = 20.0;
    const priceBottom = 245.0;
    const volumeTop = 270.0;
    final minPrice = candles.map((c) => c.low).reduce(math.min);
    final maxPrice = candles.map((c) => c.high).reduce(math.max);
    final span = maxPrice - minPrice == 0 ? 1.0 : maxPrice - minPrice;
    final chartWidth = math.max(1.0, size.width - left - right);
    final slot = chartWidth / candles.length;
    final maxVolume = candles.map((c) => c.volume).reduce(math.max).clamp(1.0, double.infinity).toDouble();
    final axis = Paint()..color = Colors.grey..strokeWidth = 1;
    canvas.drawLine(Offset(left, priceBottom), Offset(size.width - right, priceBottom), axis);
    final textStyle = TextStyle(color: Colors.grey.shade700, fontSize: 10);
    _drawText(canvas, 'High $maxPrice', Offset(left, 2), textStyle);
    _drawText(canvas, 'Low $minPrice', Offset(left, priceBottom - 12), textStyle);
    _drawText(canvas, 'Volume', Offset(left, volumeTop - 14), textStyle);
    for (var i = 0; i < candles.length; i++) {
      final c = candles[i];
      final x = left + slot * (i + 0.5);
      double y(double price) => top + ((maxPrice - price) / span) * (priceBottom - top - 10);
      final color = c.close >= c.open ? Colors.green.shade700 : Colors.red.shade700;
      final paint = Paint()..color = color..strokeWidth = 1.2;
      canvas.drawLine(Offset(x, y(c.high)), Offset(x, y(c.low)), paint);
      final bodyTop = math.min(y(c.open), y(c.close));
      final bodyHeight = math.max(1.0, (y(c.open) - y(c.close)).abs());
      canvas.drawRect(Rect.fromLTWH(x - slot * 0.3, bodyTop, math.max(1.0, slot * 0.6), bodyHeight), paint);
      final volumeHeight = (c.volume / maxVolume) * 65;
      canvas.drawRect(Rect.fromLTWH(x - slot * 0.3, volumeTop + 65 - volumeHeight, math.max(1.0, slot * 0.6), volumeHeight), Paint()..color = color.withOpacity(0.55));
    }
  }

  void _drawText(Canvas canvas, String text, Offset offset, TextStyle style) {
    final painter = TextPainter(text: TextSpan(text: text, style: style), textDirection: TextDirection.ltr)..layout();
    painter.paint(canvas, offset);
  }

  @override
  bool shouldRepaint(covariant CandleChartPainter oldDelegate) => oldDelegate.candles != candles;
}
