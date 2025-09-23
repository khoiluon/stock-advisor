import React, { useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

// Hàm tính SMA (Moving Average)
function calculateSMA(data, period) {
  const result = [];
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) continue;

    const sum = data
      .slice(i - period + 1, i + 1)
      .reduce((acc, d) => acc + parseFloat(d.Close), 0);

    result.push({
      time: data[i].date,
      value: Number((sum / period).toFixed(2)),
    });
  }
  return result;
}

// MACD calculation helper
function calculateMACD(data, fast = 12, slow = 26, signal = 9) {
  // Calculate EMA
  function ema(arr, period, key = 'Close') {
    const k = 2 / (period + 1);
    let emaArr = [];
    let prev;
    for (let i = 0; i < arr.length; i++) {
      const price = parseFloat(arr[i][key]);
      if (i === 0) {
        prev = price;
      } else {
        prev = price * k + prev * (1 - k);
      }
      emaArr.push(prev);
    }
    return emaArr;
  }
  const fastEMA = ema(data, fast);
  const slowEMA = ema(data, slow);
  const macdLine = fastEMA.map((val, i) => val - slowEMA[i]);
  // Signal line
  const signalLine = ema(macdLine.map((v, i) => ({ Close: v })), signal, 'Close');
  // Histogram
  const histogram = macdLine.map((v, i) => v - signalLine[i]);
  // Format for chart
  return data.map((d, i) => ({
    time: d.date,
    macd: macdLine[i],
    signal: signalLine[i],
    hist: histogram[i],
  }));
}

const StockChart = ({ data, maLines = [], indicators = {} }) => {
  const chartContainerRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current || !data || data.length === 0) return;
    chartContainerRef.current.innerHTML = '';

    // Khởi tạo chart
    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: '#0f172a' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: '#1e293b' },
        horzLines: { color: '#1e293b' },
      },
      width: chartContainerRef.current.clientWidth || 900,
      height: 400,
      localization: { locale: 'en-US' },
    });

    // Trục
    chart.priceScale('right').applyOptions({ borderColor: '#475569', textColor: '#94a3b8' });
    chart.timeScale().applyOptions({ borderColor: '#475569', textColor: '#94a3b8' });

    // === Candlestick ===
    const candlestickData = data.map(d => ({
      time: d.date,
      open: parseFloat(d.Open),
      high: parseFloat(d.High),
      low: parseFloat(d.Low),
      close: parseFloat(d.Close),
    }));

    const candleSeries = chart.addCandlestickSeries({
      upColor: '#22c55e',
      downColor: '#ef4444',
      borderUpColor: '#22c55e',
      borderDownColor: '#ef4444',
      wickUpColor: 'rgba(34,197,94,0.8)',
      wickDownColor: 'rgba(239,68,68,0.8)',
      priceScaleId: 'right',
    });
    candleSeries.setData(candlestickData);

    // === Moving Averages ===
    // MA colors: MA20: #38bdf8, MA50: #a78bfa, MA200: #facc15
    const maColors = {
      20: '#38bdf8',
      50: '#a78bfa',
      200: '#facc15',
    };
    maLines.forEach((maLine) => {
      const maData = calculateSMA(data, maLine.period);
      const color = maColors[maLine.period] || '#38bdf8';
      const maSeries = chart.addLineSeries({
        color,
        lineWidth: 2,
        priceScaleId: 'right',
      });
      maSeries.setData(maData);
    });

    // === Bollinger Bands ===
    if (indicators.bbands && indicators.bbands.visible) {
      const bbandsData = data.map(d => ({
        time: d.date,
        upper: parseFloat(d['BBU_20_2.0']),
        middle: parseFloat(d['BBM_20_2.0']),
        lower: parseFloat(d['BBL_20_2.0']),
      }));

      const upper = chart.addLineSeries({ color: 'rgba(59,130,246,0.5)', lineWidth: 1, priceScaleId: 'right' }); // #3b82f6
      const middle = chart.addLineSeries({ color: 'rgba(59,130,246,0.5)', lineWidth: 1, lineStyle: 2, priceScaleId: 'right' });
      const lower = chart.addLineSeries({ color: 'rgba(59,130,246,0.5)', lineWidth: 1, priceScaleId: 'right' });

      upper.setData(bbandsData.map(d => ({ time: d.time, value: d.upper })));
      middle.setData(bbandsData.map(d => ({ time: d.time, value: d.middle })));
      lower.setData(bbandsData.map(d => ({ time: d.time, value: d.lower })));
    }

    // === MACD Indicator ===
    let macdCreated = false;
    if (indicators.macd && indicators.macd.visible && indicators.rsi && indicators.rsi.visible) {
      // Nếu cả MACD và RSI đều bật, chia vùng rõ hơn
      const { fast = 12, slow = 26, signal = 9 } = indicators.macd;
      const macdData = calculateMACD(data, fast, slow, signal);
      // MACD line
      const macdSeries = chart.addLineSeries({
        color: '#38bdf8',
        lineWidth: 2,
        priceScaleId: 'macd',
      });
      macdCreated = true;
      macdSeries.setData(macdData.map(d => ({ time: d.time, value: d.macd })));
      // Signal line
      const signalSeries = chart.addLineSeries({
        color: '#a78bfa',
        lineWidth: 2,
        priceScaleId: 'macd',
        lineStyle: 2,
      });
      signalSeries.setData(macdData.map(d => ({ time: d.time, value: d.signal })));
      // Histogram
      const histSeries = chart.addHistogramSeries({
        color: '#facc15',
        priceScaleId: 'macd',
        priceFormat: { type: 'volume' },
        scaleMargins: { top: 0.7, bottom: 0 },
      });
      histSeries.setData(macdData.map(d => ({ time: d.time, value: d.hist, color: d.hist >= 0 ? '#22c55e' : '#ef4444' })));
      // Scale margins: MACD ở giữa, RSI dưới cùng
      // Chỉ gọi applyOptions nếu đã tạo series
      if (macdCreated) chart.priceScale('macd').applyOptions({ scaleMargins: { top: 0.35, bottom: 0.35 } });
      // RSI sẽ được tạo phía dưới
    } else if (indicators.macd && indicators.macd.visible) {
      // Chỉ MACD
      const { fast = 12, slow = 26, signal = 9 } = indicators.macd;
      const macdData = calculateMACD(data, fast, slow, signal);
      const macdSeries = chart.addLineSeries({
        color: '#38bdf8',
        lineWidth: 2,
        priceScaleId: 'macd',
      });
      macdCreated = true;
      macdSeries.setData(macdData.map(d => ({ time: d.time, value: d.macd })));
      const signalSeries = chart.addLineSeries({
        color: '#a78bfa',
        lineWidth: 2,
        priceScaleId: 'macd',
        lineStyle: 2,
      });
      signalSeries.setData(macdData.map(d => ({ time: d.time, value: d.signal })));
      const histSeries = chart.addHistogramSeries({
        color: '#facc15',
        priceScaleId: 'macd',
        priceFormat: { type: 'volume' },
        scaleMargins: { top: 0.7, bottom: 0 },
      });
      histSeries.setData(macdData.map(d => ({ time: d.time, value: d.hist, color: d.hist >= 0 ? '#22c55e' : '#ef4444' })));
      if (macdCreated) chart.priceScale('macd').applyOptions({ scaleMargins: { top: 0.55, bottom: 0.15 } });
    }

    // === RSI Indicator ===
    if (indicators.rsi && indicators.rsi.visible) {
      // Tạo series RSI
      const rsiSeries = chart.addLineSeries({
        color: '#fcd34d',
        lineWidth: 2,
        priceScaleId: 'rsi',
      });


      // Nếu MACD cũng bật, scaleMargins cho rsi sẽ khác
      if (macdCreated) {
        chart.priceScale('rsi').applyOptions({ scaleMargins: { top: 0.7, bottom: 0.05 } });
        chart.priceScale('right').applyOptions({ scaleMargins: { top: 0, bottom: 0.65 } });
      } else {
        chart.priceScale('rsi').applyOptions({ scaleMargins: { top: 0.70, bottom: 0.15 } });
        chart.priceScale('right').applyOptions({ scaleMargins: { top: 0, bottom: 0.30 } });
      }

      const rsiData = data
        .map(d => ({ time: d.date, value: Number(d.RSI_14) }))
        .filter(p => Number.isFinite(p.value));
      rsiSeries.setData(rsiData);

      rsiSeries.createPriceLine({
        price: 70,
        color: '#ef4444',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: 'Overbought',
      });
      rsiSeries.createPriceLine({
        price: 30,
        color: '#22c55e',
        lineWidth: 1,
        lineStyle: 2,
        axisLabelVisible: true,
        title: 'Oversold',
      });
    }

    // === Volume ===
    const volumeData = data.map(d => ({
      time: d.date,
      value: parseInt(d.Volume, 10),
      color: parseFloat(d.Close) >= parseFloat(d.Open)
        ? 'rgba(22,163,74,0.6)'
        : 'rgba(220,38,38,0.6)',
    }));

    const volumeSeries = chart.addHistogramSeries({
      color: 'rgba(22,163,74,0.6)',
      priceFormat: { type: 'volume' },
      priceScaleId: 'volume',
    });

    // Apply scale margins sau khi đã add series
    chart.priceScale('volume').applyOptions(
      indicators.rsi && indicators.rsi.visible
        ? { scaleMargins: { top: 0.85, bottom: 0 } } // nếu có RSI thì volume nằm dưới cùng
        : { scaleMargins: { top: 0.75, bottom: 0 } } // mặc định
    );

    volumeSeries.setData(volumeData);

    // Fit nội dung chart
    chart.timeScale().fitContent();

    // Resize khi thay đổi màn hình
    const handleResize = () => {
      chart.applyOptions({
        width: chartContainerRef.current.clientWidth || 900,
      });
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data, maLines, indicators]);

  return (
    <div style={{ width: '100%', maxWidth: 1200, margin: '0 auto', height: 400 }}>
      <div ref={chartContainerRef} style={{ position: 'relative', width: '100%', height: 400 }} />
    </div>
  );
};

export default StockChart;
