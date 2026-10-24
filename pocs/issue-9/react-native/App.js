import React, { useMemo, useState } from 'react';
import { SafeAreaView, ScrollView, StatusBar, StyleSheet, Text, View, Pressable } from 'react-native';

const fixture = require('./assets/ohlcv_synthetic_v1.json');

function CandleChart({ candles, scale }) {
  const geometry = useMemo(() => {
    const minPrice = Math.min(...candles.map(c => c.low));
    const maxPrice = Math.max(...candles.map(c => c.high));
    const maxVolume = Math.max(...candles.map(c => c.volume));
    const range = Math.max(maxPrice - minPrice, 1);
    return { priceY: value => 12 + ((maxPrice - value) / range) * 176, maxVolume };
  }, [candles]);
  return (
    <ScrollView horizontal accessibilityLabel="Horizontal chart viewport; scroll horizontally to pan">
      <View style={[styles.chart, { width: candles.length * 42 * scale }]}>
        {candles.map((c, index) => {
          const rising = c.close >= c.open;
          const top = geometry.priceY(Math.max(c.open, c.close));
          const bottom = geometry.priceY(Math.min(c.open, c.close));
          const wickTop = geometry.priceY(c.high);
          const wickBottom = geometry.priceY(c.low);
          return (
            <View key={c.timestamp} style={[styles.candleColumn, { width: 42 * scale }]} accessible
              accessibilityLabel={`Candle ${index + 1}, ${c.timestamp}, open ${c.open}, high ${c.high}, low ${c.low}, close ${c.close}, volume ${c.volume}`}>
              <View style={[styles.wick, { top: wickTop, height: Math.max(2, wickBottom - wickTop), backgroundColor: rising ? '#16845b' : '#c13d4a' }]} />
              <View style={[styles.body, { top, height: Math.max(3, bottom - top), width: Math.max(5, 9 * scale), backgroundColor: rising ? '#16845b' : '#c13d4a' }]} />
              <View style={[styles.volume, { height: Math.max(2, (c.volume / geometry.maxVolume) * 54), width: Math.max(5, 12 * scale), backgroundColor: rising ? '#16845b88' : '#c13d4a88' }]} />
            </View>
          );
        })}
      </View>
    </ScrollView>
  );
}

export default function App() {
  const [scale, setScale] = useState(1);
  const candles = fixture.candles;
  return (
    <SafeAreaView style={styles.screen}>
      <StatusBar barStyle="dark-content" />
      <ScrollView contentContainerStyle={styles.content}>
        <Text style={styles.title}>Crypto Intelligence</Text>
        <Text style={styles.subtitle}>React Native reference · synthetic fixture only</Text>
        <View style={styles.notice}><Text style={styles.noticeText}>Synthetic benchmark data. Not live prices or investment advice.</Text></View>
        <Text style={styles.section}>OHLCV · 5 minutes · {candles.length} candles</Text>
        <View style={styles.controls}>
          <Pressable accessibilityRole="button" accessibilityLabel="Zoom out chart" style={styles.control} onPress={() => setScale(v => Math.max(0.75, Number((v - 0.25).toFixed(2))))}><Text style={styles.controlText}>− Zoom</Text></Pressable>
          <Text accessibilityLiveRegion="polite" style={styles.scaleText}>{Math.round(scale * 100)}%</Text>
          <Pressable accessibilityRole="button" accessibilityLabel="Zoom in chart" style={styles.control} onPress={() => setScale(v => Math.min(3, Number((v + 0.25).toFixed(2))))}><Text style={styles.controlText}>+ Zoom</Text></Pressable>
        </View>
        <CandleChart candles={candles} scale={scale} />
        <Text style={styles.caption}>Scroll horizontally to pan; use zoom controls to change candle spacing.</Text>
        <Text style={styles.section}>Fixture data</Text>
        <ScrollView horizontal><View>
          <View style={styles.tableRow}>{['UTC timestamp','Open','High','Low','Close','Volume'].map(v => <Text key={v} style={[styles.cell,styles.headerCell]}>{v}</Text>)}</View>
          {candles.map(c => <View key={c.timestamp} style={styles.tableRow}>{[c.timestamp,c.open,c.high,c.low,c.close,c.volume].map((v,i)=><Text key={i} style={styles.cell}>{String(v)}</Text>)}</View>)}
        </View></ScrollView>
      </ScrollView>
    </SafeAreaView>
  );
}
const styles = StyleSheet.create({
  screen:{flex:1,backgroundColor:'#f7f8fa'},content:{padding:16,gap:12},
  title:{fontSize:24,fontWeight:'700',color:'#17212b'},subtitle:{fontSize:13,color:'#52616b'},
  notice:{backgroundColor:'#fff3cd',borderRadius:8,padding:10},noticeText:{color:'#664d03',fontSize:12},
  section:{fontSize:16,fontWeight:'700',color:'#17212b',marginTop:8},
  controls:{flexDirection:'row',alignItems:'center',gap:12},
  control:{backgroundColor:'#e5eaf0',paddingHorizontal:14,paddingVertical:8,borderRadius:8},
  controlText:{fontWeight:'600',color:'#17212b'},scaleText:{minWidth:48,textAlign:'center',fontVariant:['tabular-nums']},
  chart:{height:250,flexDirection:'row',alignItems:'stretch',backgroundColor:'#fff',borderRadius:8,borderWidth:1,borderColor:'#d9e0e7',paddingHorizontal:8,marginTop:4},
  candleColumn:{height:240,position:'relative',alignItems:'center'},wick:{position:'absolute',width:2},
  body:{position:'absolute',borderRadius:1},volume:{position:'absolute',bottom:8,borderRadius:2},
  caption:{color:'#52616b',fontSize:12},tableRow:{flexDirection:'row'},
  cell:{width:112,paddingVertical:7,paddingHorizontal:8,borderBottomWidth:1,borderColor:'#d9e0e7',color:'#17212b',fontSize:12},
  headerCell:{fontWeight:'700',backgroundColor:'#e5eaf0'}
});
