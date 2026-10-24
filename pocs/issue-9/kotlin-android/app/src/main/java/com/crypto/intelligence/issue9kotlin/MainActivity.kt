package com.crypto.intelligence.issue9kotlin

import android.app.Activity
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.HorizontalScrollView
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import org.json.JSONObject
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

private data class Candle(
    val timestamp: String,
    val open: Double,
    val high: Double,
    val low: Double,
    val close: Double,
    val volume: Double,
)

class MainActivity : Activity() {
    private lateinit var chart: CandleChartView
    private lateinit var candles: List<Candle>
    private var scale = 1.0f
    private val density: Float get() = resources.displayMetrics.density

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        candles = loadFixture()
        val page = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(16), dp(12), dp(16), dp(16))
            setBackgroundColor(Color.rgb(247, 248, 250))
        }
        page.addView(text("Kotlin chart reference", 24f, true))
        page.addView(text("Native Android reference · synthetic fixture only", 13f, false))
        page.addView(text("Synthetic benchmark data. Not live prices or investment advice.", 12f, false))
        page.addView(text("OHLCV · 5 minutes · ${candles.size} synthetic OHLCV candles", 16f, true))

        val controls = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        val zoomOut = Button(this).apply {
            text = "− Zoom"
            contentDescription = "Zoom out chart"
            setOnClickListener { setScale(max(0.75f, scale - 0.25f)) }
        }
        val zoomIn = Button(this).apply {
            text = "+ Zoom"
            contentDescription = "Zoom in chart"
            setOnClickListener { setScale(min(3.0f, scale + 0.25f)) }
        }
        val scaleLabel = TextView(this).apply {
            text = "100%"
            gravity = android.view.Gravity.CENTER_VERTICAL
            contentDescription = "Chart zoom level"
            setPadding(dp(12), 0, dp(12), 0)
        }
        controls.addView(zoomOut)
        controls.addView(scaleLabel)
        controls.addView(zoomIn)
        page.addView(controls)

        chart = CandleChartView(this, candles).apply {
            contentDescription = "Candlestick and volume chart for ${candles.size} synthetic OHLCV candles. Scroll horizontally to pan."
            importantForAccessibility = View.IMPORTANT_FOR_ACCESSIBILITY_YES
        }
        chart.tag = scaleLabel
        val viewport = HorizontalScrollView(this).apply {
            isHorizontalScrollBarEnabled = true
            contentDescription = "Horizontal chart viewport; scroll horizontally to pan"
            addView(chart, LinearLayout.LayoutParams(dp(1000), dp(320)))
        }
        page.addView(viewport)

        page.addView(text("Fixture data", 16f, true))
        val table = buildString {
            append("UTC timestamp | Open | High | Low | Close | Volume\n")
            candles.forEach { c ->
                append("${c.timestamp} | ${c.open} | ${c.high} | ${c.low} | ${c.close} | ${c.volume}\n")
            }
        }
        page.addView(text(table, 11f, false))
        val outer = ScrollView(this).apply { addView(page) }
        setContentView(outer)
        chart.scaleLabel = scaleLabel
        chart.updateScale(scale)
    }

    private fun loadFixture(): List<Candle> {
        val raw = assets.open("ohlcv_synthetic_v1.json").bufferedReader().use { it.readText() }
        val root = JSONObject(raw)
        check(root.optString("kind") == "synthetic-not-market-data") { "Fixture provenance marker is missing" }
        val items = root.getJSONArray("candles")
        return (0 until items.length()).map { i ->
            val item = items.getJSONObject(i)
            Candle(
                timestamp = item.getString("timestamp"),
                open = item.getDouble("open"),
                high = item.getDouble("high"),
                low = item.getDouble("low"),
                close = item.getDouble("close"),
                volume = item.getDouble("volume"),
            )
        }
    }

    private fun setScale(value: Float) {
        scale = value
        chart.updateScale(value)
    }

    private fun text(value: String, sizeSp: Float, bold: Boolean) = TextView(this).apply {
        text = value
        textSize = sizeSp
        setTextColor(Color.rgb(23, 33, 43))
        if (bold) setTypeface(typeface, android.graphics.Typeface.BOLD)
        setPadding(0, dp(6), 0, dp(6))
        if (value.length < 100) contentDescription = value
    }

    private fun dp(value: Int): Int = (value * density).toInt()
}

private class CandleChartView(
    private val activity: Activity,
    private val candles: List<Candle>,
) : View(activity) {
    private val density = resources.displayMetrics.density
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
    var scaleLabel: TextView? = null
    private var scale = 1.0f

    fun updateScale(value: Float) {
        scale = value
        val params = layoutParams
        if (params != null) {
            params.width = (1000 * density * scale).toInt()
            layoutParams = params
        }
        scaleLabel?.text = "${(scale * 100).toInt()}%"
        contentDescription = "Candlestick and volume chart for ${candles.size} synthetic OHLCV candles at ${(scale * 100).toInt()} percent zoom. Scroll horizontally to pan."
        invalidate()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        canvas.drawColor(Color.WHITE)
        if (candles.isEmpty()) return
        val left = 30f * density
        val right = 12f * density
        val top = 20f * density
        val priceBottom = height * 0.68f
        val volumeTop = height * 0.78f
        val volumeBottom = height - 18f * density
        val minPrice = candles.minOf { it.low }
        val maxPrice = candles.maxOf { it.high }
        val priceRange = max(maxPrice - minPrice, 1.0)
        val maxVolume = max(candles.maxOf { it.volume }, 1.0)
        val chartWidth = max(width - left - right, 1f)
        val slot = chartWidth / candles.size

        paint.color = Color.LTGRAY
        paint.strokeWidth = density
        canvas.drawLine(left, priceBottom, width - right, priceBottom, paint)
        paint.color = Color.DKGRAY
        paint.textSize = 11f * density
        canvas.drawText("High $maxPrice", left, 14f * density, paint)
        canvas.drawText("Low $minPrice", left, priceBottom - 4f * density, paint)
        canvas.drawText("Volume", left, volumeTop - 4f * density, paint)

        candles.forEachIndexed { index, candle ->
            val x = left + slot * (index + 0.5f)
            fun y(price: Double) = top + ((maxPrice - price) / priceRange).toFloat() * (priceBottom - top - 12f * density)
            val rising = candle.close >= candle.open
            val color = if (rising) Color.rgb(22, 132, 91) else Color.rgb(193, 61, 74)
            paint.color = color
            paint.strokeWidth = max(1.2f * density, 1f)
            canvas.drawLine(x, y(candle.high), x, y(candle.low), paint)
            val bodyTop = min(y(candle.open), y(candle.close))
            val bodyHeight = max(abs(y(candle.open) - y(candle.close)), 2f * density)
            canvas.drawRect(x - slot * 0.28f, bodyTop, x + slot * 0.28f, bodyTop + bodyHeight, paint)
            val volumeHeight = (candle.volume / maxVolume).toFloat() * (volumeBottom - volumeTop)
            paint.alpha = 150
            canvas.drawRect(x - slot * 0.28f, volumeBottom - volumeHeight, x + slot * 0.28f, volumeBottom, paint)
            paint.alpha = 255
        }
    }
}
